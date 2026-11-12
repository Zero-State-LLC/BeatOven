"""Adapters: the four existing "to hardware" contracts -> one Output Stream.

Each adapter is a pure function. None of them changes the source contract.
Where a source leaves a unit or meaning undefined, the caller must state it;
the adapter never guesses. Inputs that cannot be mapped are listed in the
stream's ``notes`` as UNROUTED or NOT_COMPUTABLE instead of being dropped
silently.
"""

from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .contract import Channel, ChannelKind, ContractError, Op, OutputEvent, OutputStream

SEMITONE_UV = Decimal(1_000_000) / Decimal(12)
RETRIGGER_GAP_US = 1_000

PITCH0, PITCH1 = Channel(ChannelKind.PITCH_CV, 0), Channel(ChannelKind.PITCH_CV, 1)
CLOCK0, RESET0 = Channel(ChannelKind.CLOCK, 0), Channel(ChannelKind.RESET, 0)


def _gate(i: int) -> Channel:
    return Channel(ChannelKind.GATE, i)


def _mod(i: int) -> Channel:
    return Channel(ChannelKind.MOD_CV, i)


# role -> (pitch channel or None, gate channel, drums-as-triggers)
DEFAULT_ROLE_ROUTING: Dict[str, Tuple[Optional[Channel], Channel, bool]] = {
    "DRUMS": (None, _gate(0), True),
    "BASS": (PITCH0, _gate(1), False),
    "MELODY": (PITCH1, _gate(2), False),
    "HARMONY": (None, _gate(3), False),
}


def _sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _dec(x: Any) -> Decimal:
    return Decimal(str(x))


def _round(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def note_to_uv(note: int, zero_volt_note: int) -> int:
    """1 V/oct: microvolts for a MIDI note, given the note that sits at 0 V."""
    return _round(Decimal(note - zero_volt_note) * SEMITONE_UV)


def unit_to_uv(v: Any, lo_uv: int = 0, hi_uv: int = 5_000_000) -> int:
    """Map a unitless 0..1 value onto an explicit voltage span."""
    d = _dec(v)
    if not 0 <= d <= 1:
        raise ContractError(f"unitless value outside [0, 1]: {v}")
    return _round(Decimal(lo_uv) + d * Decimal(hi_uv - lo_uv))


class _Timebase:
    """Convert a source time value into microseconds. The unit is always explicit."""

    def __init__(self, unit: str, bpm: Any = None, beats_per_bar: Any = None) -> None:
        if unit == "seconds":
            self.us_per_unit = Decimal(1_000_000)
        elif unit == "beats":
            self.us_per_unit = Decimal(60_000_000) / _dec(bpm)
        elif unit == "bars":
            self.us_per_unit = Decimal(60_000_000) / _dec(bpm) * _dec(beats_per_bar)
        else:
            raise ContractError(f"time unit must be 'beats', 'bars' or 'seconds', got {unit!r}")

    def us(self, t: Any) -> int:
        return _round(_dec(t) * self.us_per_unit)


def _clock_period_us(bpm: Any, ppqn: int) -> int:
    return _round(Decimal(60_000_000) / (_dec(bpm) * ppqn))


_CLOCK_PULSE_US = 5_000  # the OutputStream default clock pulse width


def _clock_stop_us(stop: int, period: int, since: int = 0) -> int:
    """Earliest time >= ``stop`` at which the clock's last pulse has ended.

    A clock that started at ``since`` ticks every ``period``. Stopping inside a
    pulse would leave the stream ending with the clock jack still high.
    """
    stop = max(stop, since + period)
    last_tick = since + (stop - since) // period * period
    return max(stop, last_tick + min(_CLOCK_PULSE_US, period // 2))


def _notes_to_events(
    notes: Sequence[Tuple[int, int, int]],  # (t_on_us, t_off_us, midi note), any order
    pitch: Optional[Channel], gate: Channel, as_trigger: bool,
    zero_volt_note: int, trigger_us: int,
) -> List[OutputEvent]:
    """Monophonic, last-note priority. An overlapped note is cut 1 ms before the next."""
    out: List[OutputEvent] = []
    ordered = sorted(notes)
    for i, (t_on, t_off, note) in enumerate(ordered):
        if as_trigger:
            out.append(OutputEvent(t_on, gate, Op.PULSE, trigger_us))
            continue
        if i + 1 < len(ordered) and ordered[i + 1][0] < t_off + RETRIGGER_GAP_US:
            t_off = ordered[i + 1][0] - RETRIGGER_GAP_US
        if t_off <= t_on:
            continue  # shorter than the retrigger gap: not playable as a gate
        if pitch is not None:
            out.append(OutputEvent(t_on, pitch, Op.SET_UV, note_to_uv(note, zero_volt_note)))
        out.append(OutputEvent(t_on, gate, Op.GATE_ON))
        out.append(OutputEvent(t_off, gate, Op.GATE_OFF))
    return out


def _dedupe(events: Iterable[OutputEvent]) -> List[OutputEvent]:
    seen, out = set(), []
    for e in events:
        if e.sort_key() not in seen:
            seen.add(e.sort_key())
            out.append(e)
    return out


def from_pack(
    pack: Mapping[str, Any],
    *,
    time_unit: str = "bars",
    zero_volt_note: int = 12,
    clock_ppqn: Optional[int] = 24,
    trigger_us: int = 5_000,
    reset_at_start: bool = True,
    role_routing: Mapping[str, Tuple[Optional[Channel], Channel, bool]] = DEFAULT_ROLE_ROUTING,
) -> OutputStream:
    """BeatOven Pack v0 -> Output Stream.

    The Pack's ``t`` and ``dur`` are in bars (operator decision B1,
    2026-11-12); ``time_unit`` stays as an override. The clock is derived from
    ``midi.tempo_bpm`` at ``clock_ppqn`` pulses per quarter note, 24 by default
    (decisions B2, B3). ``cv.clock_hz`` is never used. Pass ``clock_ppqn=None``
    for no clock.
    """
    midi = pack["midi"]
    bpm = midi["tempo_bpm"]
    sig = midi["time_signature"]
    beats_per_bar = Decimal(sig["num"]) * Decimal(4) / Decimal(sig["den"])
    tb = _Timebase(time_unit, bpm, beats_per_bar)
    events: List[OutputEvent] = []
    notes: List[str] = []

    for idx, track in enumerate(midi["tracks"]):
        role = track["instrument_role"]
        route = role_routing.get(role)
        if route is None:
            notes.append(f"UNROUTED: track role {role} has no output")
        else:
            pitch, gate, as_trigger = route
            if pitch is None and not as_trigger:
                notes.append(f"UNROUTED: pitch of role {role} (gate only on {gate.name})")
            spans = [
                (tb.us(n["t"]), tb.us(_dec(n["t"]) + _dec(n["dur"])), int(n["pitch"]))
                for clip in track["clips"] for n in clip["notes"]
            ]
            events += _notes_to_events(spans, pitch, gate, as_trigger, zero_volt_note, trigger_us)
        for lane in track.get("cc_lanes", []):
            if idx > 3:
                notes.append(f"UNROUTED: cc lane {lane['meaning']} (no MOD_CV left)")
                continue
            for p in lane["points"]:
                events.append(OutputEvent(tb.us(p["t"]), _mod(idx), Op.SET_UV, unit_to_uv(_dec(p["v"]) / 127)))

    cv = pack.get("cv") or {}
    period: Optional[int] = None
    if clock_ppqn is not None:
        period = _clock_period_us(bpm, clock_ppqn)
        if cv.get("clock_hz") is not None:
            notes.append("NOT_COMPUTABLE: cv.clock_hz ignored; it is not derived from midi.tempo_bpm")
    elif cv.get("clock_hz") is not None:
        notes.append("NOT_COMPUTABLE: cv.clock_hz ignored and no clock_ppqn given; no clock is emitted")
    for lane in cv.get("lanes", []):
        kind = lane["lane_type"]
        if kind == "MOD_CV":
            for p in lane["points"]:
                events.append(OutputEvent(tb.us(p["t"]), _mod(4), Op.SET_UV, unit_to_uv(p["v"])))
        elif kind == "CLOCK":
            notes.append("NOT_COMPUTABLE: CLOCK lane points have no defined meaning; clock comes from a rate")
        else:
            notes.append(f"NOT_COMPUTABLE: {kind} lane values have no defined unit in beatoven.pack.v0")

    events = _dedupe(events)
    end = max((e.t_us for e in events), default=0)
    if reset_at_start:
        events.append(OutputEvent(0, RESET0, Op.PULSE, trigger_us))
    if period is not None:
        events.append(OutputEvent(0, CLOCK0, Op.CLOCK_PERIOD, period))
        events.append(OutputEvent(_clock_stop_us(end, period), CLOCK0, Op.CLOCK_PERIOD, 0))
    return OutputStream.build(
        events, source_contract="beatoven.pack.v0", source_hash=_sha(pack),
        seed=pack.get("seed"), notes=tuple(notes),
    )


DEFAULT_MACRO_ROUTING: Dict[str, int] = {
    "energy": 0, "density": 1, "tension": 2, "brightness": 3, "complexity": 4, "emotional_intensity": 5,
}
_RHYTHM_GATES = (("kick", 0), ("snare", 1), ("hat", 2), ("perc", 3))


def from_resonance_frame(
    frame: Any,
    *,
    bars: int,
    step_threshold: Optional[float] = None,
    clock_ppqn: int = 24,
    trigger_us: int = 5_000,
    macro_routing: Mapping[str, int] = DEFAULT_MACRO_ROUTING,
) -> OutputStream:
    """ResonanceFrame -> Output Stream.

    A RhythmTokens step value is a velocity (operator decision B10,
    2026-11-12): a step fires when its value is above 0. ``step_threshold``
    stays as an override; when given, a step fires when its value is >= it.
    Swing is not applied.
    """
    events: List[OutputEvent] = []
    notes: List[str] = []
    metrics = getattr(frame, "metrics", None)
    if metrics is not None:
        for name in ("complexity", "emotional_intensity", "groove", "energy",
                     "density", "swing", "brightness", "tension"):
            if name in macro_routing:
                events.append(OutputEvent(0, _mod(macro_routing[name]), Op.SET_UV,
                                          unit_to_uv(getattr(metrics, name))))
            else:
                notes.append(f"UNROUTED: metric {name}")
    rhythm = getattr(frame, "rhythm", None)
    if rhythm is not None:
        num, den = rhythm.meter
        bar_us = Decimal(60_000_000) / _dec(rhythm.bpm) * Decimal(num) * Decimal(4) / Decimal(den)
        for name, gate_i in _RHYTHM_GATES:
            grid = getattr(rhythm, name)
            if not grid:
                continue
            for bar in range(bars):
                for step, v in enumerate(grid):
                    fires = _dec(v) > 0 if step_threshold is None else _dec(v) >= _dec(step_threshold)
                    if fires:
                        t = _round(bar_us * bar + bar_us * step / len(grid))
                        events.append(OutputEvent(t, _gate(gate_i), Op.PULSE, trigger_us))
        period = _clock_period_us(rhythm.bpm, clock_ppqn)
        events.append(OutputEvent(0, CLOCK0, Op.CLOCK_PERIOD, period))
        events.append(OutputEvent(_clock_stop_us(_round(bar_us * bars), period), CLOCK0, Op.CLOCK_PERIOD, 0))
        if metrics is not None:
            notes.append("NOT_COMPUTABLE: swing is not applied; its timing meaning is undefined")
    source = {"id": getattr(frame, "id", None), "provenance_hash": getattr(frame, "provenance_hash", None)}
    return OutputStream.build(
        events, source_contract="ResonanceFrame",
        source_hash=getattr(frame, "provenance_hash", None) or _sha(source), notes=tuple(notes),
    )


_ACF_FIELDS = ("rhythm_density", "spectral_centroid", "harmonic_tension", "modulation_rate", "silence_probability")


def _get(obj: Any, key: str) -> Any:
    return obj[key] if isinstance(obj, Mapping) else getattr(obj, key)


def from_audio_control_frames(frames: Sequence[Any], *, window_us: int, clock_ppqn: int = 24) -> OutputStream:
    """AudioControlFrame sequence -> Output Stream.

    ``window_us`` is required: ``window_utc`` identifies a window but the
    contract does not give its playback length.
    """
    if window_us <= 0:
        raise ContractError("window_us must be positive")
    events: List[OutputEvent] = []
    last_period: Optional[int] = None
    last_change = 0
    for i, frame in enumerate(frames):
        t = i * window_us
        period = _clock_period_us(_get(frame, "tempo_bpm"), clock_ppqn)
        if period != last_period:
            events.append(OutputEvent(t, CLOCK0, Op.CLOCK_PERIOD, period))
            last_period, last_change = period, t
        for ch, name in enumerate(_ACF_FIELDS):
            events.append(OutputEvent(t, _mod(ch), Op.SET_UV, unit_to_uv(_get(frame, name))))
    if frames:
        events.append(OutputEvent(_clock_stop_us(len(frames) * window_us, last_period, last_change), CLOCK0, Op.CLOCK_PERIOD, 0))
    digest = _sha([{k: _get(f, k) for k in ("window_utc", "tempo_bpm") + _ACF_FIELDS} for f in frames])
    return OutputStream.build(events, source_contract="AudioControlFrame", source_hash=digest)


def from_cv_gate_map(cv_gate_map: Mapping[str, Any], *, cycles: int = 1, trigger_us: int = 5_000) -> OutputStream:
    """BeatOvenOverlay ``cv_gate_map`` -> Output Stream. One pattern character per clock period."""
    period = _round(Decimal(1_000_000) / _dec(cv_gate_map["clock_hz"]))
    pattern = cv_gate_map["gate_pattern"]
    if set(pattern) - {"0", "1"}:
        raise ContractError("gate_pattern must contain only '0' and '1'")
    events = [OutputEvent(0, CLOCK0, Op.CLOCK_PERIOD, period)]
    for cycle in range(cycles):
        for step, bit in enumerate(pattern):
            if bit == "1":
                events.append(OutputEvent((cycle * len(pattern) + step) * period, _gate(0), Op.PULSE, trigger_us))
    events.append(OutputEvent(cycles * len(pattern) * period, CLOCK0, Op.CLOCK_PERIOD, 0))
    return OutputStream.build(events, source_contract="cv_gate_map", source_hash=_sha(dict(cv_gate_map)))


# MIDI channel (0-based) -> role, mirroring the Pack's track order.
DEFAULT_MIDI_CHANNEL_ROLES: Dict[int, str] = {0: "DRUMS", 1: "BASS", 2: "HARMONY", 3: "MELODY"}


def from_midi_event_stream(
    stream: Mapping[str, Any],
    *,
    ppq: Optional[int] = None,
    tempo_bpm: Any = None,
    zero_volt_note: int = 12,
    trigger_us: int = 5_000,
    channel_roles: Mapping[int, str] = DEFAULT_MIDI_CHANNEL_ROLES,
    role_routing: Mapping[str, Tuple[Optional[Channel], Channel, bool]] = DEFAULT_ROLE_ROUTING,
) -> OutputStream:
    """MIDIEventStream.v1 -> Output Stream.

    Canon leaves ``events`` as an empty array. This adapter reads the PROPOSED
    item shape ``{"t": int, "status": int, "data1": int, "data2": int}``;
    see plan.md for the proposal.
    """
    if stream.get("schema_version") != "MIDIEventStream.v1":
        raise ContractError("not a MIDIEventStream.v1")
    mode = stream.get("sync_mode")
    if mode == "wall_clock":
        us_per_t = Decimal(1)
    elif mode in ("absolute_tick", "delta_time"):
        if ppq is None or tempo_bpm is None:
            raise ContractError(f"sync_mode {mode} needs ppq and tempo_bpm")
        us_per_t = Decimal(60_000_000) / (_dec(tempo_bpm) * ppq)
    else:
        raise ContractError(f"unknown sync_mode: {mode!r}")

    notes: List[str] = []
    events: List[OutputEvent] = []
    open_notes: Dict[Tuple[int, int], int] = {}
    spans: Dict[int, List[Tuple[int, int, int]]] = {}
    acc = 0
    for item in stream.get("events", []):
        acc = acc + int(item["t"]) if mode == "delta_time" else int(item["t"])
        t = _round(Decimal(acc) * us_per_t)
        status, d1, d2 = int(item["status"]), int(item.get("data1", 0)), int(item.get("data2", 0))
        kind, ch = status & 0xF0, status & 0x0F
        if kind == 0x90 and d2 > 0:
            open_notes[(ch, d1)] = t
        elif kind == 0x80 or (kind == 0x90 and d2 == 0):
            t_on = open_notes.pop((ch, d1), None)
            if t_on is not None:
                spans.setdefault(ch, []).append((t_on, t, d1))
        elif kind == 0xB0 and ch <= 3:
            events.append(OutputEvent(t, _mod(ch), Op.SET_UV, unit_to_uv(Decimal(d2) / 127)))
        else:
            notes.append(f"UNROUTED: MIDI status {status:#04x}")
    if open_notes:
        raise ContractError(f"{len(open_notes)} note-on without note-off")
    for ch, ch_spans in sorted(spans.items()):
        route = role_routing.get(channel_roles.get(ch, ""))
        if route is None:
            notes.append(f"UNROUTED: MIDI channel {ch}")
            continue
        events += _notes_to_events(ch_spans, route[0], route[1], route[2], zero_volt_note, trigger_us)
    return OutputStream.build(
        _dedupe(events), source_contract="MIDIEventStream.v1",
        source_hash=_sha(dict(stream)), notes=tuple(sorted(set(notes))),
    )
