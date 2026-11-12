"""Real MIDI port transport (USB-MIDI, or any port the OS exposes).

Needs the optional ``python-rtmidi`` package. This transport is not
simulated: the driver refuses to use it without a Hardware Lane Grant.

``SimulatedPortDevice`` puts the simulated Output Module behind a pair of
virtual MIDI ports, so the whole host path (driver, OS MIDI stack, SysEx
framing) can be exercised with no hardware attached.
"""

from __future__ import annotations

import threading
import time
from typing import List, Optional

from .sim import SimulatedOutputModule
from .wire import SYSEX_END, SYSEX_START


def _rtmidi():
    try:
        import rtmidi
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise RuntimeError("python-rtmidi is not installed (pip install python-rtmidi)") from exc
    return rtmidi


def list_ports() -> dict:
    rt = _rtmidi()
    return {"out": rt.MidiOut().get_ports(), "in": rt.MidiIn().get_ports()}


def _open(port, name: str, kind: str):
    names = port.get_ports()
    matches = [i for i, n in enumerate(names) if name in n]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one MIDI {kind} port matching {name!r}, found {len(matches)}: {names}")
    port.open_port(matches[0])
    return port


class MidiPortTransport:
    """Sends each wire frame as one SysEx message; returns received SysEx bytes."""

    simulated = False

    def __init__(self, out_name: str, in_name: Optional[str] = None) -> None:
        rt = _rtmidi()
        self._out = _open(rt.MidiOut(), out_name, "output")
        self._in = None
        if in_name is not None:
            self._in = _open(rt.MidiIn(), in_name, "input")
            self._in.ignore_types(sysex=False, timing=True, active_sense=True)

    def send(self, data: bytes) -> None:
        if not data or data[0] != SYSEX_START or data[-1] != SYSEX_END:
            raise ValueError("transport carries whole SysEx frames only")
        self._out.send_message(list(data))

    def recv(self) -> bytes:
        if self._in is None:
            return b""
        out = bytearray()
        while True:
            msg = self._in.get_message()
            if msg is None:
                return bytes(out)
            out.extend(msg[0])

    def close(self) -> None:
        self._out.close_port()
        if self._in is not None:
            self._in.close_port()


class SimulatedPortDevice:
    """The simulated Output Module behind two virtual MIDI ports, on real time."""

    def __init__(self, name: str = "Output Module Sim", device: Optional[SimulatedOutputModule] = None) -> None:
        rt = _rtmidi()
        self.device = device or SimulatedOutputModule()
        self.host_to_device = f"{name} RX"   # the host opens this as its output
        self.device_to_host = f"{name} TX"   # the host opens this as its input
        self._in = rt.MidiIn()
        self._in.ignore_types(sysex=False, timing=True, active_sense=True)
        self._in.open_virtual_port(self.host_to_device)
        self._out = rt.MidiOut()
        self._out.open_virtual_port(self.device_to_host)
        self.transit_us: List[int] = []      # arrival time minus the time the frame carried, SYNC frames only
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @staticmethod
    def _now() -> int:
        return time.monotonic_ns() // 1000

    def _run(self) -> None:
        while not self._stop.is_set():
            got = False
            while True:
                msg = self._in.get_message()
                if msg is None:
                    break
                got = True
                self.device.feed(bytes(msg[0]), self._now())
            self.device.advance(self._now())
            out = self.device.take_output()
            start = 0
            while start < len(out):
                end = out.index(SYSEX_END, start)
                self._out.send_message(list(out[start:end + 1]))
                start = end + 1
            if not got:
                time.sleep(0.0002)

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)
        self._in.close_port()
        self._out.close_port()
