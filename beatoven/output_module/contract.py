"""Canonical hardware contract: the Output Stream.

One schema (``beatoven.output_stream.v1``) that every "to hardware" path
compiles into. It carries explicit units: time in microseconds, CV in
microvolts, pulse widths in microseconds. Nothing in it is unitless.

The stream is plain data. It grants no authority to drive hardware; see
``authority.py`` for the hardware lane gate.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, Iterable, List, Optional, Tuple

CONTRACT_VERSION = "beatoven.output_stream.v1"
DESCRIPTOR_VERSION = "beatoven.output_module_descriptor.v1"

MIN_PULSE_US = 1_000          # trigger length floor: 1 ms
MAX_PULSE_US = 10_000_000     # 10 s
MIN_CLOCK_PERIOD_US = 1_000
MAX_T_US = (1 << 40) - 1      # ~12.7 days; fits the 5-byte wire field after packing
INT32_MIN, INT32_MAX = -(1 << 31), (1 << 31) - 1

# Wire record: t_us (u64), op (u8), channel id (u8), value (i32). Big-endian.
RECORD = struct.Struct(">QBBi")


class ContractError(ValueError):
    """The stream or descriptor violates the contract. Always fail closed."""


class ChannelKind(str, Enum):
    PITCH_CV = "PITCH_CV"
    MOD_CV = "MOD_CV"
    GATE = "GATE"
    CLOCK = "CLOCK"
    RESET = "RESET"


class Op(IntEnum):
    SET_UV = 1         # value: microvolts at the jack
    GATE_ON = 2        # value: 0
    GATE_OFF = 3       # value: 0
    PULSE = 4          # value: width in microseconds
    CLOCK_PERIOD = 5   # value: period in microseconds; 0 stops the clock


_KIND_BASE = {
    ChannelKind.PITCH_CV: 0x00,
    ChannelKind.MOD_CV: 0x10,
    ChannelKind.GATE: 0x20,
    ChannelKind.CLOCK: 0x30,
    ChannelKind.RESET: 0x40,
}
_BASE_KIND = {v: k for k, v in _KIND_BASE.items()}

ALLOWED_OPS = {
    ChannelKind.PITCH_CV: {Op.SET_UV},
    ChannelKind.MOD_CV: {Op.SET_UV},
    ChannelKind.GATE: {Op.GATE_ON, Op.GATE_OFF, Op.PULSE},
    ChannelKind.CLOCK: {Op.CLOCK_PERIOD, Op.PULSE},
    ChannelKind.RESET: {Op.PULSE},
}


@dataclass(frozen=True, order=True)
class Channel:
    kind: ChannelKind
    index: int

    def __post_init__(self) -> None:
        if not 0 <= self.index <= 15:
            raise ContractError(f"channel index out of range: {self.index}")

    @property
    def wire_id(self) -> int:
        return _KIND_BASE[self.kind] + self.index

    @property
    def name(self) -> str:
        return f"{self.kind.value}:{self.index}"

    @staticmethod
    def parse(name: str) -> "Channel":
        try:
            kind, index = name.split(":")
            return Channel(ChannelKind(kind), int(index))
        except (ValueError, KeyError) as exc:
            raise ContractError(f"bad channel name: {name!r}") from exc

    @staticmethod
    def from_wire(wire_id: int) -> "Channel":
        base = wire_id & 0xF0
        if base not in _BASE_KIND:
            raise ContractError(f"bad channel id: {wire_id:#x}")
        return Channel(_BASE_KIND[base], wire_id & 0x0F)


@dataclass(frozen=True)
class OutputEvent:
    t_us: int
    channel: Channel
    op: Op
    value: int = 0

    def sort_key(self) -> Tuple[int, int, int, int]:
        return (self.t_us, self.channel.wire_id, int(self.op), self.value)

    def pack(self) -> bytes:
        return RECORD.pack(self.t_us, int(self.op), self.channel.wire_id, self.value)

    @staticmethod
    def unpack(raw: bytes) -> "OutputEvent":
        t_us, op, wire_id, value = RECORD.unpack(raw)
        try:
            return OutputEvent(t_us, Channel.from_wire(wire_id), Op(op), value)
        except ValueError as exc:
            raise ContractError(f"bad record: {raw.hex()}") from exc

    def to_dict(self) -> Dict[str, Any]:
        return {"t_us": self.t_us, "ch": self.channel.name, "op": self.op.name, "value": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "OutputEvent":
        try:
            return OutputEvent(int(d["t_us"]), Channel.parse(d["ch"]), Op[d["op"]], int(d.get("value", 0)))
        except KeyError as exc:
            raise ContractError(f"bad event: {d!r}") from exc


def _validate_event(e: OutputEvent) -> None:
    if not 0 <= e.t_us <= MAX_T_US:
        raise ContractError(f"t_us out of range: {e.t_us}")
    if e.op not in ALLOWED_OPS[e.channel.kind]:
        raise ContractError(f"{e.op.name} is not allowed on {e.channel.name}")
    if e.op is Op.SET_UV and not INT32_MIN <= e.value <= INT32_MAX:
        raise ContractError(f"microvolt value out of int32 range: {e.value}")
    if e.op is Op.PULSE and not MIN_PULSE_US <= e.value <= MAX_PULSE_US:
        raise ContractError(f"pulse width {e.value} us outside [{MIN_PULSE_US}, {MAX_PULSE_US}]")
    if e.op is Op.CLOCK_PERIOD and e.value != 0 and not MIN_CLOCK_PERIOD_US <= e.value <= MAX_PULSE_US:
        raise ContractError(f"clock period out of range: {e.value} us")
    if e.op in (Op.GATE_ON, Op.GATE_OFF) and e.value != 0:
        raise ContractError("gate events carry value 0")


@dataclass(frozen=True)
class OutputStream:
    """An ordered, validated, content-addressed sequence of Output Events."""

    events: Tuple[OutputEvent, ...]
    source_contract: str                 # e.g. "beatoven.pack.v0"
    source_hash: str                     # sha256 hex of the source object
    seed: Optional[int] = None
    clock_pulse_us: int = 5_000          # width of each generated clock pulse
    notes: Tuple[str, ...] = ()          # adapter notes: unrouted or NOT_COMPUTABLE inputs

    def __post_init__(self) -> None:
        if not MIN_PULSE_US <= self.clock_pulse_us <= MAX_PULSE_US:
            raise ContractError("clock_pulse_us out of range")
        prev: Optional[Tuple[int, int, int, int]] = None
        for e in self.events:
            _validate_event(e)
            key = e.sort_key()
            if prev is not None and key < prev:
                raise ContractError("events are not in canonical order")
            if prev is not None and key == prev:
                raise ContractError(f"duplicate event at t_us={e.t_us} on {e.channel.name}")
            prev = key

    @staticmethod
    def build(events: Iterable[OutputEvent], **header: Any) -> "OutputStream":
        """Sort into canonical order, then validate."""
        return OutputStream(events=tuple(sorted(events, key=OutputEvent.sort_key)), **header)

    @property
    def duration_us(self) -> int:
        return self.events[-1].t_us if self.events else 0

    def channels(self) -> List[Channel]:
        return sorted({e.channel for e in self.events})

    def header_bytes(self) -> bytes:
        return b"|".join([
            CONTRACT_VERSION.encode(),
            self.source_contract.encode(),
            self.source_hash.encode(),
            b"" if self.seed is None else str(self.seed).encode(),
            str(self.clock_pulse_us).encode(),
            str(len(self.events)).encode(),
        ])

    def canonical_bytes(self) -> bytes:
        return self.header_bytes() + b"\n" + b"".join(e.pack() for e in self.events)

    @property
    def stream_id(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": CONTRACT_VERSION,
            "stream_id": f"sha256:{self.stream_id}",
            "source": {"contract": self.source_contract, "hash": self.source_hash, "seed": self.seed},
            "clock_pulse_us": self.clock_pulse_us,
            "duration_us": self.duration_us,
            "notes": list(self.notes),
            "events": [e.to_dict() for e in self.events],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "OutputStream":
        if d.get("schema") != CONTRACT_VERSION:
            raise ContractError(f"unsupported schema: {d.get('schema')!r}")
        try:
            src = d["source"]
            stream = OutputStream(
                events=tuple(OutputEvent.from_dict(e) for e in d["events"]),
                source_contract=src["contract"],
                source_hash=src["hash"],
                seed=src.get("seed"),
                clock_pulse_us=int(d.get("clock_pulse_us", 5_000)),
                notes=tuple(d.get("notes", ())),
            )
        except (KeyError, TypeError) as exc:
            raise ContractError(f"malformed stream: {exc}") from exc
        claimed = d.get("stream_id")
        if claimed is not None and claimed != f"sha256:{stream.stream_id}":
            raise ContractError("stream_id does not match content")
        return stream


class SafePolicy(str, Enum):
    HOLD = "HOLD"                  # keep the last value
    SLEW_TO_SAFE = "SLEW_TO_SAFE"  # move to safe_uv over safe_slew_us


@dataclass(frozen=True)
class ChannelSpec:
    channel: Channel
    min_uv: int = 0
    max_uv: int = 0
    bits: int = 0
    safe_policy: SafePolicy = SafePolicy.HOLD
    safe_uv: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.channel.name, "min_uv": self.min_uv, "max_uv": self.max_uv,
            "bits": self.bits, "safe_policy": self.safe_policy.value, "safe_uv": self.safe_uv,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ChannelSpec":
        return ChannelSpec(
            Channel.parse(d["id"]), int(d.get("min_uv", 0)), int(d.get("max_uv", 0)),
            int(d.get("bits", 0)), SafePolicy(d.get("safe_policy", "HOLD")), int(d.get("safe_uv", 0)),
        )

    def quantize(self, uv: int) -> Tuple[int, int]:
        """Return (DAC code, microvolts actually produced). Integer math only."""
        full = (1 << self.bits) - 1
        span = self.max_uv - self.min_uv
        code = ((uv - self.min_uv) * full * 2 + span) // (2 * span)
        return code, self.min_uv + (code * span * 2 + full) // (2 * full)


@dataclass(frozen=True)
class Descriptor:
    """What one Output Module can do. The device reports it; the host never guesses."""

    device: str
    firmware: str
    channels: Tuple[ChannelSpec, ...]
    contract_versions: Tuple[str, ...] = (CONTRACT_VERSION,)
    queue_capacity: int = 1024
    max_events_per_frame: int = 16
    min_lead_us: int = 5_000
    keepalive_timeout_us: int = 300_000
    sync_timeout_us: int = 2_000_000
    safe_slew_us: int = 50_000
    # Optional (ADRs 0005, 0006). Absent from the dict means the device does not support it.
    clock_in: bool = False
    calibration: Optional[str] = None  # "identity" or "stored"

    def spec(self, channel: Channel) -> Optional[ChannelSpec]:
        for s in self.channels:
            if s.channel == channel:
                return s
        return None

    def check_stream(self, stream: OutputStream) -> None:
        """Raise ContractError unless this device can play the stream exactly."""
        for e in stream.events:
            spec = self.spec(e.channel)
            if spec is None:
                raise ContractError(f"device has no channel {e.channel.name}")
            if e.op is Op.SET_UV and not spec.min_uv <= e.value <= spec.max_uv:
                raise ContractError(
                    f"{e.value} uV on {e.channel.name} is outside [{spec.min_uv}, {spec.max_uv}] uV"
                )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema": DESCRIPTOR_VERSION, "device": self.device, "firmware": self.firmware,
            "contract_versions": list(self.contract_versions),
            "channels": [c.to_dict() for c in self.channels],
            "queue_capacity": self.queue_capacity, "max_events_per_frame": self.max_events_per_frame,
            "min_lead_us": self.min_lead_us, "keepalive_timeout_us": self.keepalive_timeout_us,
            "sync_timeout_us": self.sync_timeout_us, "safe_slew_us": self.safe_slew_us,
        }
        if self.clock_in:
            d["clock_in"] = True
        if self.calibration is not None:
            d["calibration"] = self.calibration
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Descriptor":
        if d.get("schema") != DESCRIPTOR_VERSION:
            raise ContractError(f"unsupported descriptor schema: {d.get('schema')!r}")
        try:
            return Descriptor(
                device=d["device"], firmware=d["firmware"],
                channels=tuple(ChannelSpec.from_dict(c) for c in d["channels"]),
                contract_versions=tuple(d["contract_versions"]),
                queue_capacity=int(d["queue_capacity"]),
                max_events_per_frame=int(d["max_events_per_frame"]),
                min_lead_us=int(d["min_lead_us"]),
                keepalive_timeout_us=int(d["keepalive_timeout_us"]),
                sync_timeout_us=int(d["sync_timeout_us"]),
                safe_slew_us=int(d["safe_slew_us"]),
                clock_in=d.get("clock_in", False) is True,
                calibration=_calibration_state(d.get("calibration")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(f"malformed descriptor: {exc}") from exc


CALIBRATION_STATES = ("identity", "stored")


def _calibration_state(value: Any) -> Optional[str]:
    if value is None:
        return None
    if value not in CALIBRATION_STATES:
        raise ValueError(f"bad calibration state: {value!r}")
    return value


def reference_descriptor(device: str = "sim", firmware: str = "sim-0.1.0") -> Descriptor:
    """The PROPOSED channel set: 2 pitch, 6 mod CV, 4 gate, 1 clock, 1 reset.

    Ranges are proposals pending the open clarifications in the spec.
    """
    chans: List[ChannelSpec] = []
    for i in range(2):
        chans.append(ChannelSpec(Channel(ChannelKind.PITCH_CV, i), 0, 10_000_000, 16, SafePolicy.HOLD))
    for i in range(6):
        chans.append(ChannelSpec(
            Channel(ChannelKind.MOD_CV, i), -5_000_000, 5_000_000, 16, SafePolicy.SLEW_TO_SAFE, 0))
    for i in range(4):
        chans.append(ChannelSpec(Channel(ChannelKind.GATE, i)))
    chans.append(ChannelSpec(Channel(ChannelKind.CLOCK, 0)))
    chans.append(ChannelSpec(Channel(ChannelKind.RESET, 0)))
    return Descriptor(device=device, firmware=firmware, channels=tuple(chans), clock_in=True, calibration="identity")
