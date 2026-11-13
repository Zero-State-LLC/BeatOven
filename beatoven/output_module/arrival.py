"""Play-on-arrival mapping: plain MIDI bytes to Output Events (PROPOSED, ADR 0007).

NON_DETERMINISTIC: events take the time the bytes arrived, so transport jitter
reaches the jacks and two runs differ. Nothing here is an Output Stream: there
is no stream id, no played hash and no replay check.

This module is a pure function of its input. It drives no hardware and no
device uses it yet; whether a device may is the operator's ruling (ADR 0007).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .contract import Channel, ChannelKind, Descriptor, Op, OutputEvent, reference_descriptor

LABEL = "NON_DETERMINISTIC"

VOICE_CHANNELS = (0, 1)          # MIDI channels 1 and 2
TRIGGER_CHANNEL = 9              # MIDI channel 10
TRIGGER_NOTES = {36: 2, 38: 3}   # note -> GATE index
MOD_CHANNEL = 0                  # MIDI channel 1
MOD_CCS = {1: 0, 2: 1, 16: 2, 17: 3, 18: 4, 19: 5}  # controller -> MOD_CV index
MOD_FULL_UV = 5_000_000
BEND_SEMITONES = 2
ACTIVE_SENSING_TIMEOUT_US = 300_000

_DATA_BYTES = {0x80: 2, 0x90: 2, 0xA0: 2, 0xB0: 2, 0xC0: 1, 0xD0: 1, 0xE0: 2}
_SYSTEM_DATA_BYTES = {0xF1: 1, 0xF2: 2, 0xF3: 1}


class ArrivalMapper:
    """Turn a MIDI byte stream into Output Events stamped with their arrival time."""

    def __init__(self, descriptor: Optional[Descriptor] = None, *, zero_volt_note: int = 12,
                 trigger_us: int = 5_000) -> None:
        self.descriptor = descriptor or reference_descriptor()
        self.zero_volt_note = zero_volt_note
        self.trigger_us = trigger_us
        self._status = 0
        self._data: List[int] = []
        self._in_sysex = False
        self._held: Dict[int, List[int]] = {v: [] for v in VOICE_CHANNELS}
        self._bend: Dict[int, int] = {v: 0 for v in VOICE_CHANNELS}
        self._last_tick: Optional[int] = None
        self._last_rx: Optional[int] = None
        self._sensing = False

    # ---- input --------------------------------------------------------------
    def feed(self, data: bytes, t_us: int) -> List[OutputEvent]:
        """Consume bytes that arrived at ``t_us``. Returns the events to play now."""
        out: List[OutputEvent] = []
        for b in data:
            self._last_rx = t_us
            if b >= 0xF8:                       # real-time: may appear anywhere
                self._realtime(b, t_us, out)
            elif b == 0xF0:
                self._in_sysex, self._status = True, 0
            elif b >= 0x80:
                self._in_sysex = False
                self._status = 0 if b in (0xF6, 0xF7) else b
                self._data = []
            elif self._in_sysex or not self._status:
                continue
            else:
                self._data.append(b)
                need = _SYSTEM_DATA_BYTES.get(self._status) or _DATA_BYTES[self._status & 0xF0]
                if len(self._data) == need:
                    if self._status < 0xF0:
                        self._voice_message(self._status, self._data, t_us, out)
                    else:
                        self._status = 0        # system common has no running status
                    self._data = []
        return out

    def tick(self, t_us: int) -> List[OutputEvent]:
        """Call as time passes. Gates go low if Active Sensing was seen and has stopped."""
        if self._sensing and self._last_rx is not None and t_us - self._last_rx >= ACTIVE_SENSING_TIMEOUT_US:
            self._sensing = False
            return self._all_gates_off(t_us)
        return []

    # ---- messages -----------------------------------------------------------
    def _realtime(self, b: int, t: int, out: List[OutputEvent]) -> None:
        if b == 0xF8:
            width = self.trigger_us
            if self._last_tick is not None and t - self._last_tick < 2 * self.trigger_us:
                width = max(1_000, (t - self._last_tick) // 2)
            self._last_tick = t
            out.append(OutputEvent(t, Channel(ChannelKind.CLOCK, 0), Op.PULSE, width))
        elif b == 0xFA:
            out.append(OutputEvent(t, Channel(ChannelKind.RESET, 0), Op.PULSE, self.trigger_us))
        elif b in (0xFC, 0xFF):
            out.extend(self._all_gates_off(t))
        elif b == 0xFE:
            self._sensing = True

    def _voice_message(self, status: int, d: List[int], t: int, out: List[OutputEvent]) -> None:
        kind, ch = status & 0xF0, status & 0x0F
        if kind == 0x90 and d[1] > 0:
            if ch in self._held:
                self._note_on(ch, d[0], t, out)
            elif ch == TRIGGER_CHANNEL and d[0] in TRIGGER_NOTES:
                out.append(OutputEvent(t, Channel(ChannelKind.GATE, TRIGGER_NOTES[d[0]]), Op.PULSE, self.trigger_us))
        elif kind in (0x80, 0x90):
            if ch in self._held:
                self._note_off(ch, d[0], t, out)
        elif kind == 0xE0 and ch in self._held:
            self._bend[ch] = (d[1] << 7 | d[0]) - 8192
            if self._held[ch]:
                self._set_pitch(ch, self._held[ch][-1], t, out)
        elif kind == 0xB0:
            if d[0] in (120, 123) and ch in self._held:
                self._voice_off(ch, t, out)
            elif ch == MOD_CHANNEL and d[0] in MOD_CCS:
                uv = (d[1] * MOD_FULL_UV * 2 + 127) // 254
                out.append(OutputEvent(t, Channel(ChannelKind.MOD_CV, MOD_CCS[d[0]]), Op.SET_UV, uv))

    # ---- voices -------------------------------------------------------------
    def _pitch_uv(self, voice: int, note: int) -> Optional[int]:
        """Microvolts for a note with the voice's bend, or None if the jack cannot produce it."""
        num = (note - self.zero_volt_note) * 8192 + self._bend[voice] * BEND_SEMITONES
        den = 12 * 8192
        uv = (num * 1_000_000 * 2 + den) // (2 * den)
        spec = self.descriptor.spec(Channel(ChannelKind.PITCH_CV, voice))
        if spec is None or not spec.min_uv <= uv <= spec.max_uv:
            return None
        return uv

    def _set_pitch(self, voice: int, note: int, t: int, out: List[OutputEvent]) -> bool:
        uv = self._pitch_uv(voice, note)
        if uv is None:
            return False
        out.append(OutputEvent(t, Channel(ChannelKind.PITCH_CV, voice), Op.SET_UV, uv))
        return True

    def _note_on(self, voice: int, note: int, t: int, out: List[OutputEvent]) -> None:
        if not self._set_pitch(voice, note, t, out):
            return
        was_held = bool(self._held[voice])
        if note in self._held[voice]:
            self._held[voice].remove(note)
        self._held[voice].append(note)
        if not was_held:
            out.append(OutputEvent(t, Channel(ChannelKind.GATE, voice), Op.GATE_ON))

    def _note_off(self, voice: int, note: int, t: int, out: List[OutputEvent]) -> None:
        held = self._held[voice]
        if note not in held:
            return
        was_top = held[-1] == note
        held.remove(note)
        if not held:
            out.append(OutputEvent(t, Channel(ChannelKind.GATE, voice), Op.GATE_OFF))
        elif was_top:
            self._set_pitch(voice, held[-1], t, out)

    def _voice_off(self, voice: int, t: int, out: List[OutputEvent]) -> None:
        if self._held[voice]:
            self._held[voice].clear()
            out.append(OutputEvent(t, Channel(ChannelKind.GATE, voice), Op.GATE_OFF))

    def _all_gates_off(self, t: int) -> List[OutputEvent]:
        out: List[OutputEvent] = []
        for voice in VOICE_CHANNELS:
            self._voice_off(voice, t, out)
        return out
