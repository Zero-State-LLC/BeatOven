"""Simulated Output Module.

A software stand-in for the device: it speaks the wire protocol, runs the
lifecycle and the timestamped scheduler on a virtual clock, and records a
jack trace (every level or voltage change with its exact time). The trace is
what a logic analyzer or scope would see on ideal hardware, so two runs can
be diffed. It is a model, not a measurement.
"""

from __future__ import annotations

import hashlib
import heapq
import struct
from typing import Dict, List, Optional, Tuple

import cbor2

from .contract import Channel, ChannelKind, ContractError, Descriptor, Op, OutputEvent, SafePolicy, reference_descriptor
from .lifecycle import Event, Lifecycle, LossReason, State
from .wire import Frame, Msg, WireError, parse_events_body, split_frames

TraceEntry = Tuple[int, str, str, int]  # (device t_us, jack, kind, value)
_REASONS = list(LossReason)
_STATES = list(State)

# Heap priorities at equal time: internal falling edges, then stream events, then clock ticks.
_P_OFF, _P_EVENT, _P_CLOCK = 0, 1, 2


class SimulatedOutputModule:
    def __init__(self, descriptor: Optional[Descriptor] = None, clock_offset_us: int = 0) -> None:
        self.descriptor = descriptor or reference_descriptor()
        self.clock_offset_us = clock_offset_us  # device clock = host clock + offset
        self.lifecycle = Lifecycle()
        self.trace: List[TraceEntry] = []
        self.loss_reason: Optional[LossReason] = None
        self.ops_log: List[dict] = []
        self._rx = bytearray()
        self._tx: List[bytes] = []
        self._heap: List[tuple] = []
        self._n = 0
        self._now = clock_offset_us
        self._last_rx = self._last_sync = clock_offset_us
        self._start = 0
        self._expected = self._received = self._played = 0
        self._stream_id = b""
        self._clock_pulse_us = 5_000
        self._clock_gen = 0
        self._pulse_gen: Dict[str, int] = {}
        self._hash = hashlib.sha256()
        self._safe_at: Optional[int] = None
        self._cv: Dict[str, int] = {}
        self._levels: Dict[str, int] = {}
        self._tx_seq = 0

    # ---- transport side -------------------------------------------------
    def feed(self, data: bytes, host_now_us: int) -> None:
        self.advance(host_now_us)
        self._rx.extend(data)
        for raw in split_frames(self._rx):
            self._last_rx = self._now
            try:
                frame = Frame.decode(raw)
            except WireError:
                if self.lifecycle.state is State.STREAMING:
                    self._lose(LossReason.INTEGRITY)
                continue
            self._handle(frame)

    def take_output(self) -> bytes:
        out, self._tx = b"".join(self._tx), []
        return out

    def detach(self) -> None:
        if self.lifecycle.can(Event.DETACH):
            self._outputs_safe(slew=False)
            self.lifecycle.fire(Event.DETACH)

    # ---- time -------------------------------------------------------------
    def advance(self, host_now_us: int) -> None:
        target = host_now_us + self.clock_offset_us
        while self._heap and self._heap[0][0] <= target:
            t, _prio, _n, action = heapq.heappop(self._heap)
            self._now = t
            action(t)
        self._now = max(self._now, target)
        st = self.lifecycle.state
        if st is State.STREAMING and self._received < self._expected \
                and self._now - self._last_rx > self.descriptor.keepalive_timeout_us:
            self._lose(LossReason.KEEPALIVE_TIMEOUT)
        elif st is State.SYNCED and self._now - self._last_sync > self.descriptor.sync_timeout_us:
            self._lose(LossReason.SYNC_TIMEOUT)
        if self.lifecycle.state is State.TIMING_LOST and self._safe_at is not None and self._now >= self._safe_at:
            self._safe_at = None
            self.lifecycle.fire(Event.SAFE_REACHED)
            self._send_status()

    # ---- protocol ---------------------------------------------------------
    def _send(self, mtype: Msg, body: bytes) -> None:
        self._tx.append(Frame(mtype, self._tx_seq, body).encode())
        self._tx_seq = (self._tx_seq + 1) & 0x7F

    def _send_status(self) -> None:
        reason = 0 if self.loss_reason is None else _REASONS.index(self.loss_reason) + 1
        self._send(Msg.STATUS, struct.pack(">BBI", _STATES.index(self.lifecycle.state), reason, self._played))

    def _ack(self, frame: Frame, ok: bool) -> None:
        self._send(Msg.ACK, bytes([frame.seq, 1 if ok else 0]))

    def _handle(self, f: Frame) -> None:
        st = self.lifecycle.state
        if f.type is Msg.HELLO:
            if st is State.DISCONNECTED:
                self._outputs_safe(slew=False)
                self.lifecycle.fire(Event.ATTACH)
            self._send(Msg.DESCRIPTOR, cbor2.dumps(self.descriptor.to_dict()))
        elif f.type is Msg.SYNC:
            self._send(Msg.SYNC_ACK, f.body[:8] + struct.pack(">Q", self._now))
            self._last_sync = self._now
            if st is State.ENUMERATING:
                self.lifecycle.fire(Event.SYNC_OK)
            elif st is State.SAFE_IDLE:
                self.loss_reason = None
                self.lifecycle.fire(Event.RESYNC)
        elif f.type is Msg.STREAM_BEGIN:
            stream_id, count, start, pulse = struct.unpack(">32sIQI", f.body)
            ok = st is State.SYNCED and start >= self._now + self.descriptor.min_lead_us
            if ok:
                self._stream_id, self._expected, self._start, self._clock_pulse_us = stream_id, count, start, pulse
                self._received = self._played = 0
                self._hash = hashlib.sha256()
                self.lifecycle.fire(Event.STREAM_BEGIN)
                if count == 0:
                    self._finish()
            self._ack(f, ok)
        elif f.type is Msg.EVENTS:
            if st is not State.STREAMING:
                self._ack(f, False)
                return
            try:
                first, events = parse_events_body(f.body)
            except ContractError:
                self._lose(LossReason.INTEGRITY)
                return
            if first != self._received:
                self._lose(LossReason.SEQUENCE_GAP)
                return
            if len(self._heap) + len(events) > self.descriptor.queue_capacity:
                self._lose(LossReason.QUEUE_OVERFLOW)
                return
            for e in events:
                due = self._start + e.t_us
                if due < self._now:
                    self._lose(LossReason.LATE_EVENT)
                    return
                self._push(due, _P_EVENT, lambda t, e=e: self._play(t, e))
            self._received += len(events)
            self._ack(f, True)
        elif f.type is Msg.ABORT:
            if st is State.STREAMING:
                self._lose(LossReason.HOST_ABORT)
        elif f.type is Msg.OPS:
            msg = cbor2.loads(f.body)
            self.ops_log.append(msg)
            self._send(Msg.OPS_ACK, cbor2.dumps({"ack": msg.get("nonce"), "ok": msg.get("kind") == "PING"}))

    # ---- scheduler and outputs ---------------------------------------------
    def _push(self, t: int, prio: int, action) -> None:
        self._n += 1
        heapq.heappush(self._heap, (t, prio, self._n, action))

    def _level(self, t: int, jack: str, level: int) -> None:
        if self._levels.get(jack, 0) != level:
            self._levels[jack] = level
            self.trace.append((t, jack, "LEVEL", level))

    def _pulse(self, t: int, jack: str, width: int) -> None:
        gen = self._pulse_gen[jack] = self._pulse_gen.get(jack, 0) + 1
        self._level(t, jack, 1)
        self._push(t + width, _P_OFF, lambda t2: self._pulse_gen.get(jack) == gen and self._level(t2, jack, 0))

    def _play(self, t: int, e: OutputEvent) -> None:
        if self.lifecycle.state is not State.STREAMING:
            return
        jack = e.channel.name
        if e.op is Op.SET_UV:
            spec = self.descriptor.spec(e.channel)
            code, uv = spec.quantize(e.value)
            self._cv[jack] = uv
            self.trace.append((t, jack, "CV_UV", uv))
        elif e.op is Op.GATE_ON:
            self._pulse_gen[jack] = self._pulse_gen.get(jack, 0) + 1
            self._level(t, jack, 1)
        elif e.op is Op.GATE_OFF:
            self._pulse_gen[jack] = self._pulse_gen.get(jack, 0) + 1
            self._level(t, jack, 0)
        elif e.op is Op.PULSE:
            self._pulse(t, jack, e.value)
        elif e.op is Op.CLOCK_PERIOD:
            self._clock_gen += 1
            if e.value:
                self._clock_tick(t, jack, e.value, self._clock_gen)
        self._hash.update(e.pack())
        self._played += 1
        if self._played == self._expected:
            self._finish()

    def _clock_tick(self, t: int, jack: str, period: int, gen: int) -> None:
        if gen != self._clock_gen or self.lifecycle.state is not State.STREAMING:
            return
        self._pulse(t, jack, min(self._clock_pulse_us, period // 2))
        self._push(t + period, _P_CLOCK, lambda t2: self._clock_tick(t2, jack, period, gen))

    def _finish(self) -> None:
        self._clock_gen += 1
        self.lifecycle.fire(Event.STREAM_END)
        self._last_sync = self._now
        self._send(Msg.STREAM_DONE, self._stream_id[:8] + struct.pack(">I", self._played) + self._hash.digest())

    def _outputs_safe(self, slew: bool) -> None:
        """Fail closed: gates, clock and reset low now; CV per channel policy."""
        self._heap.clear()
        self._clock_gen += 1
        self._pulse_gen = {k: v + 1 for k, v in self._pulse_gen.items()}
        for spec in self.descriptor.channels:
            jack = spec.channel.name
            if spec.channel.kind in (ChannelKind.GATE, ChannelKind.CLOCK, ChannelKind.RESET):
                self._level(self._now, jack, 0)
            elif spec.safe_policy is SafePolicy.SLEW_TO_SAFE and self._cv.get(jack, spec.safe_uv) != spec.safe_uv:
                self.trace.append((self._now, jack, "SLEW_TO_UV" if slew else "CV_UV", spec.safe_uv))
                self._cv[jack] = spec.safe_uv

    def _lose(self, reason: LossReason) -> None:
        self.loss_reason = reason
        self.lifecycle.fire(Event.TIMING_LOSS)
        self._outputs_safe(slew=True)
        self._safe_at = self._now + self.descriptor.safe_slew_us
        self._send_status()

    # ---- evidence -----------------------------------------------------------
    def trace_csv(self, relative_to_stream: bool = True) -> str:
        """One line per change: ``t_us,jack,kind,value``. Times relative to stream start."""
        base = self._start if relative_to_stream else 0
        return "t_us,jack,kind,value\n" + "".join(f"{t - base},{j},{k},{v}\n" for t, j, k, v in self.trace)

    def trace_hash(self) -> str:
        return hashlib.sha256(self.trace_csv().encode()).hexdigest()
