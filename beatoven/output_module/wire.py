"""Wire encoding: Output Stream messages inside MIDI System Exclusive frames.

The same bytes travel over USB-MIDI (primary) and TRS MIDI (fallback).

    F0 7D 'B' 'O' <proto> <type> <seq> <7-bit packed (body + CRC16)> F7

0x7D is the MIDI non-commercial manufacturer ID. A shipped product needs its
own ID; that is an open clarification in the spec.

The Ops lane survives unchanged as data: an OPS message body is the same CBOR
map the serial Ops lane sends ({kind, nonce, payload}); only the framing
differs (SysEx envelope instead of a u32 length prefix).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterator, List, Sequence

from .contract import RECORD, ContractError, OutputEvent

SYSEX_START, SYSEX_END = 0xF0, 0xF7
MANUFACTURER = 0x7D
MAGIC = b"BO"
PROTO = 1


class Msg(IntEnum):
    # host -> device
    HELLO = 0x01
    SYNC = 0x02
    STREAM_BEGIN = 0x03
    EVENTS = 0x04
    ABORT = 0x05
    OPS = 0x06
    # device -> host
    DESCRIPTOR = 0x41
    SYNC_ACK = 0x42
    ACK = 0x43
    STATUS = 0x44
    OPS_ACK = 0x45
    STREAM_DONE = 0x46


class WireError(ContractError):
    pass


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def pack7(data: bytes) -> bytes:
    """8-bit to 7-bit: each group of up to 7 bytes gains a leading byte of MSBs."""
    out = bytearray()
    for i in range(0, len(data), 7):
        chunk = data[i:i + 7]
        msbs = 0
        for j, b in enumerate(chunk):
            msbs |= ((b >> 7) & 1) << j
        out.append(msbs)
        out.extend(b & 0x7F for b in chunk)
    return bytes(out)


def unpack7(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 8):
        group = data[i:i + 8]
        if len(group) < 2:
            raise WireError("truncated 7-bit group")
        msbs = group[0]
        for j, b in enumerate(group[1:]):
            if b & 0x80:
                raise WireError("data byte has bit 7 set")
            out.append(b | (((msbs >> j) & 1) << 7))
    return bytes(out)


@dataclass(frozen=True)
class Frame:
    type: Msg
    seq: int
    body: bytes

    def encode(self) -> bytes:
        if not 0 <= self.seq <= 0x7F:
            raise WireError("seq out of range")
        packed = pack7(self.body + struct.pack(">H", crc16(self.body)))
        return bytes([SYSEX_START, MANUFACTURER]) + MAGIC + bytes([PROTO, int(self.type), self.seq]) + packed + bytes([SYSEX_END])

    @staticmethod
    def decode(raw: bytes) -> "Frame":
        if len(raw) < 11 or raw[0] != SYSEX_START or raw[-1] != SYSEX_END:
            raise WireError("not a SysEx frame")
        if raw[1] != MANUFACTURER or raw[2:4] != MAGIC:
            raise WireError("not an Output Stream frame")
        if raw[4] != PROTO:
            raise WireError(f"unsupported protocol version {raw[4]}")
        try:
            mtype = Msg(raw[5])
        except ValueError as exc:
            raise WireError(f"unknown message type {raw[5]:#x}") from exc
        payload = unpack7(raw[7:-1])
        body, (crc,) = payload[:-2], struct.unpack(">H", payload[-2:])
        if crc16(body) != crc:
            raise WireError("CRC mismatch")
        return Frame(mtype, raw[6], body)


def split_frames(buf: bytearray) -> Iterator[bytes]:
    """Pop complete SysEx frames off the front of a byte buffer."""
    while True:
        try:
            start = buf.index(SYSEX_START)
        except ValueError:
            buf.clear()
            return
        try:
            end = buf.index(SYSEX_END, start)
        except ValueError:
            del buf[:start]
            return
        frame = bytes(buf[start:end + 1])
        del buf[:end + 1]
        yield frame


def events_body(first_index: int, events: Sequence[OutputEvent]) -> bytes:
    return struct.pack(">IB", first_index, len(events)) + b"".join(e.pack() for e in events)


def parse_events_body(body: bytes) -> tuple:
    if len(body) < 5:
        raise WireError("short EVENTS body")
    first_index, count = struct.unpack(">IB", body[:5])
    if len(body) != 5 + count * RECORD.size:
        raise WireError("EVENTS body length does not match its count")
    events: List[OutputEvent] = [
        OutputEvent.unpack(body[5 + i * RECORD.size: 5 + (i + 1) * RECORD.size]) for i in range(count)
    ]
    return first_index, events
