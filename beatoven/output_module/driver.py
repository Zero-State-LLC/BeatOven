"""Host-side driver for the Output Module.

Enumerate, sync clocks, then feed timestamped events ahead of their due time.
The device plays them on its own clock, so link jitter does not reach the
jacks as long as events arrive before they are due.
"""

from __future__ import annotations

import hashlib
import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional, Protocol

import cbor2

from .authority import HardwareLaneDenied, HardwareLaneGrant, require_hardware_lane
from .contract import CONTRACT_VERSION, ContractError, Descriptor, OutputStream
from .lifecycle import Event, Lifecycle, LossReason, State
from .sim import SimulatedOutputModule
from .wire import Frame, Msg, WireError, events_body, split_frames

_STATES = list(State)
_REASONS = list(LossReason)


class Clock(Protocol):
    def now_us(self) -> int: ...
    def sleep_until(self, t_us: int) -> None: ...


class VirtualClock:
    def __init__(self, start_us: int = 0) -> None:
        self.t = start_us

    def now_us(self) -> int:
        return self.t

    def sleep_until(self, t_us: int) -> None:
        self.t = max(self.t, t_us)


class MonotonicClock:
    def now_us(self) -> int:
        return time.monotonic_ns() // 1000

    def sleep_until(self, t_us: int) -> None:
        delay = (t_us - self.now_us()) / 1_000_000
        if delay > 0:
            time.sleep(delay)


class Transport(Protocol):
    simulated: bool
    def send(self, data: bytes) -> None: ...
    def recv(self) -> bytes: ...
    def close(self) -> None: ...


class LoopbackTransport:
    """Connects the driver to a SimulatedOutputModule on a shared clock."""

    simulated = True

    def __init__(self, device: SimulatedOutputModule, clock: Clock, delay_us: int = 0) -> None:
        self.device, self.clock, self.delay_us = device, clock, delay_us
        self.drop_next = 0  # fault injection for tests

    def send(self, data: bytes) -> None:
        if self.drop_next:
            self.drop_next -= 1
            return
        self.device.feed(data, self.clock.now_us() + self.delay_us)

    def recv(self) -> bytes:
        self.device.advance(self.clock.now_us())
        return self.device.take_output()

    def close(self) -> None:
        self.device.detach()


class OneWayLoopbackTransport:
    """A link with no return path and a byte rate, like TRS MIDI at 31.25 kbaud.

    Each frame reaches the device after the line has carried all of its bytes.
    """

    simulated = True

    def __init__(self, device: SimulatedOutputModule, clock: Clock, byte_us: int = 320) -> None:
        self.device, self.clock, self.byte_us = device, clock, byte_us
        self._line_free_at = 0

    def send(self, data: bytes) -> None:
        begin = max(self.clock.now_us(), self._line_free_at)
        self._line_free_at = begin + len(data) * self.byte_us
        self.device.feed(data, self._line_free_at)

    def recv(self) -> bytes:
        self.device.take_output()
        return b""

    def close(self) -> None:
        self.device.detach()


@dataclass
class PlayReport:
    stream_id: str
    ok: bool
    final_state: State
    played: int = 0
    played_hash_ok: bool = False
    loss_reason: Optional[LossReason] = None
    detail: str = ""
    confirmed: bool = True  # False on a one-way link: the host saw no reply


class OutputModuleDriver:
    def __init__(
        self,
        transport: Transport,
        clock: Optional[Clock] = None,
        grant: Optional[HardwareLaneGrant] = None,
        lookahead_us: int = 50_000,
        lead_us: int = 20_000,
        sync_interval_us: int = 250_000,
        reply_timeout_us: int = 1_000_000,
    ) -> None:
        self.transport = transport
        self.clock = clock or MonotonicClock()
        self.grant = grant
        self.lookahead_us, self.lead_us = lookahead_us, lead_us
        self.sync_interval_us, self.reply_timeout_us = sync_interval_us, reply_timeout_us
        self.lifecycle = Lifecycle()
        self.descriptor: Optional[Descriptor] = None
        self.offset_us = 0  # device clock minus host clock
        self.reject_reason = ""
        self._seq = 0
        self._rx = bytearray()
        self._inbox: List[Frame] = []
        self._last_sync = 0
        self._nonce = 1

    # ---- plumbing ---------------------------------------------------------
    def _send(self, mtype: Msg, body: bytes = b"") -> int:
        seq = self._seq
        self._seq = (self._seq + 1) & 0x7F
        self.transport.send(Frame(mtype, seq, body).encode())
        return seq

    def _poll(self) -> None:
        self._rx.extend(self.transport.recv())
        for raw in split_frames(self._rx):
            try:
                self._inbox.append(Frame.decode(raw))
            except WireError:
                continue  # a corrupt reply is treated as no reply

    def _take(self, mtype: Msg) -> Optional[Frame]:
        for i, f in enumerate(self._inbox):
            if f.type is mtype:
                return self._inbox.pop(i)
        return None

    def _wait(self, mtype: Msg) -> Optional[Frame]:
        deadline = self.clock.now_us() + self.reply_timeout_us
        while True:
            self._poll()
            f = self._take(mtype)
            if f is not None or self.clock.now_us() >= deadline:
                return f
            self.clock.sleep_until(self.clock.now_us() + 500)

    def _sync(self) -> bool:
        t0 = self.clock.now_us()
        self._send(Msg.SYNC, struct.pack(">Q", t0))
        ack = self._wait(Msg.SYNC_ACK)
        if ack is None:
            return False
        echoed, device_t = struct.unpack(">QQ", ack.body)
        if echoed != t0:
            return False
        rtt = self.clock.now_us() - t0
        self.offset_us = device_t - t0 - rtt // 2
        self._last_sync = self.clock.now_us()
        return True

    # ---- lifecycle ----------------------------------------------------------
    def connect(self) -> State:
        """DISCONNECTED -> ENUMERATING -> SYNCED, or SAFE_IDLE on rejection."""
        self.lifecycle.fire(Event.ATTACH)
        try:
            require_hardware_lane(self.grant, simulated=getattr(self.transport, "simulated", False))
        except HardwareLaneDenied as exc:
            return self._reject(str(exc))
        self._send(Msg.HELLO)
        reply = self._wait(Msg.DESCRIPTOR)
        if reply is None:
            return self._reject("no Descriptor from device")
        try:
            desc = Descriptor.from_dict(cbor2.loads(reply.body))
        except (ContractError, ValueError) as exc:
            return self._reject(f"bad Descriptor: {exc}")
        if CONTRACT_VERSION not in desc.contract_versions:
            return self._reject(f"device does not speak {CONTRACT_VERSION}")
        self.descriptor = desc
        if not self._sync():
            return self._reject("clock sync failed")
        return self.lifecycle.fire(Event.SYNC_OK)

    def _reject(self, reason: str) -> State:
        self.reject_reason = reason
        return self.lifecycle.fire(Event.REJECT)

    def resync(self) -> State:
        """SAFE_IDLE -> SYNCED after a fresh sync exchange. Never automatic."""
        if self.lifecycle.state is not State.SAFE_IDLE or self.descriptor is None:
            self.lifecycle.fire(Event.RESYNC)  # raises IllegalTransition
        if self._sync():
            self.lifecycle.fire(Event.RESYNC)
        return self.lifecycle.state

    def close(self) -> None:
        if self.lifecycle.can(Event.DETACH):
            self.lifecycle.fire(Event.DETACH)
        self.transport.close()

    def ops(self, kind: str, payload: Optional[dict] = None) -> bool:
        """Ops lane message: same CBOR map as SerialOpsLane, in a SysEx envelope."""
        nonce, self._nonce = self._nonce, self._nonce + 1
        self._send(Msg.OPS, cbor2.dumps({"kind": kind, "nonce": nonce, "payload": payload or {}}))
        reply = self._wait(Msg.OPS_ACK)
        if reply is None:
            return False
        ack = cbor2.loads(reply.body)
        return ack.get("ack") == nonce and bool(ack.get("ok"))

    # ---- playback -----------------------------------------------------------
    def play(self, stream: OutputStream) -> PlayReport:
        sid = stream.stream_id
        if self.lifecycle.state is not State.SYNCED or self.descriptor is None:
            self.lifecycle.fire(Event.STREAM_BEGIN)  # raises IllegalTransition
        desc = self.descriptor
        desc.check_stream(stream)  # raises ContractError; state stays SYNCED

        start_host = self.clock.now_us() + max(self.lead_us, desc.min_lead_us * 2)
        seq = self._send(Msg.STREAM_BEGIN, struct.pack(
            ">32sIQI", bytes.fromhex(sid), len(stream.events), start_host + self.offset_us, stream.clock_pulse_us))
        ack = self._wait(Msg.ACK)
        if ack is None or ack.body != bytes([seq, 1]):
            return PlayReport(sid, False, self.lifecycle.state, detail="device refused STREAM_BEGIN")
        self.lifecycle.fire(Event.STREAM_BEGIN)

        expected = hashlib.sha256(b"".join(e.pack() for e in stream.events)).digest()
        events, idx, batch = stream.events, 0, desc.max_events_per_frame
        while True:
            now = self.clock.now_us()
            while idx < len(events) and start_host + events[idx].t_us <= now + self.lookahead_us:
                chunk = events[idx: idx + batch]
                chunk = [e for e in chunk if start_host + e.t_us <= now + self.lookahead_us]
                self._send(Msg.EVENTS, events_body(idx, chunk))
                idx += len(chunk)
            self._poll()
            status = self._take(Msg.STATUS)
            if status is not None:
                state_i, reason_i, played = struct.unpack(">BBI", status.body)
                return self._lost(sid, _STATES[state_i], _REASONS[reason_i - 1] if reason_i else None, played)
            done = self._take(Msg.STREAM_DONE)
            if done is not None:
                played = struct.unpack(">I", done.body[8:12])[0]
                hash_ok = done.body[:8] == bytes.fromhex(sid)[:8] and done.body[12:] == expected
                self.lifecycle.fire(Event.STREAM_END)
                return PlayReport(sid, hash_ok and played == len(events), self.lifecycle.state, played, hash_ok,
                                  detail="" if hash_ok else "played hash mismatch")
            self._inbox = [f for f in self._inbox if f.type not in (Msg.ACK, Msg.SYNC_ACK)]
            if now - self._last_sync >= self.sync_interval_us:
                self._send(Msg.SYNC, struct.pack(">Q", now))
                self._last_sync = now
            wake = now + self.sync_interval_us
            if idx < len(events):
                wake = min(wake, start_host + events[idx].t_us - self.lookahead_us)
            else:
                wake = min(wake, max(now + 1_000, start_host + stream.duration_us))
            self.clock.sleep_until(max(wake, now + 500))
            if self.clock.now_us() > start_host + stream.duration_us + self.reply_timeout_us:
                self._send(Msg.ABORT)
                return self._lost(sid, State.TIMING_LOST, LossReason.KEEPALIVE_TIMEOUT, 0)

    def play_one_way(
        self, stream: OutputStream, descriptor: Descriptor, *,
        lead_us: int = 1_000_000, lookahead_us: int = 750_000, events_per_frame: int = 4,
    ) -> PlayReport:
        """Play over a link with no return path (TRS MIDI in).

        The device starts ``lead_us`` after it receives the begin message and
        times every event from there, so playback is still scheduled. The host
        gets no Descriptor, no status and no played hash: the operator states
        which ``descriptor`` the device has, and the report is unconfirmed.
        If the link is too slow for the stream, the device fails closed.
        """
        if self.lifecycle.state is not State.DISCONNECTED:
            self.lifecycle.fire(Event.ATTACH)  # raises IllegalTransition
        require_hardware_lane(self.grant, simulated=getattr(self.transport, "simulated", False))
        descriptor.check_stream(stream)
        sid = stream.stream_id
        self.descriptor = descriptor
        self.lifecycle.fire(Event.ATTACH)
        self._send(Msg.HELLO)
        self._send(Msg.SYNC, struct.pack(">Q", self.clock.now_us()))
        self.lifecycle.fire(Event.SYNC_OK)
        self._send(Msg.STREAM_BEGIN_REL, struct.pack(
            ">32sIQI", bytes.fromhex(sid), len(stream.events), lead_us, stream.clock_pulse_us))
        self.lifecycle.fire(Event.STREAM_BEGIN)
        start_host = self.clock.now_us() + lead_us
        events, idx = stream.events, 0
        last_keepalive = self.clock.now_us()
        while idx < len(events):
            now = self.clock.now_us()
            if start_host + events[idx].t_us <= now + lookahead_us:
                chunk = events[idx: idx + events_per_frame]
                self._send(Msg.EVENTS, events_body(idx, chunk))
                idx += len(chunk)
                last_keepalive = now
                continue
            if now - last_keepalive >= self.sync_interval_us:
                self._send(Msg.SYNC, struct.pack(">Q", now))
                last_keepalive = now
            self.clock.sleep_until(min(start_host + events[idx].t_us - lookahead_us,
                                       last_keepalive + self.sync_interval_us))
        self.clock.sleep_until(start_host + stream.duration_us + 1_000)
        self.lifecycle.fire(Event.STREAM_END)
        return PlayReport(sid, True, self.lifecycle.state, len(events), False, None,
                          "sent on a one-way link; not confirmed by the device", confirmed=False)

    def _lost(self, sid: str, device_state: State, reason: Optional[LossReason], played: int) -> PlayReport:
        self.lifecycle.fire(Event.TIMING_LOSS)
        deadline = self.clock.now_us() + self.reply_timeout_us
        while device_state is not State.SAFE_IDLE and self.clock.now_us() < deadline:
            self.clock.sleep_until(self.clock.now_us() + 5_000)
            self._poll()
            status = self._take(Msg.STATUS)
            if status is not None:
                device_state = _STATES[status.body[0]]
        if device_state is State.SAFE_IDLE:
            self.lifecycle.fire(Event.SAFE_REACHED)
        return PlayReport(sid, False, self.lifecycle.state, played, False, reason, "timing lost; outputs failed closed")
