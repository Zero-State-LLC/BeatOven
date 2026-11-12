"""Integration test over the operating system's MIDI stack, using virtual ports.

Skipped where python-rtmidi or a MIDI backend is unavailable. It runs in real
time, so it asserts on correctness (identical jack trace, played hash), not on
latency figures.
"""

import json
import time

import pytest

rtmidi = pytest.importorskip("rtmidi")

from beatoven.output_module import (  # noqa: E402
    HardwareLaneGrant, LoopbackTransport, OutputModuleDriver, SimulatedOutputModule, State, VirtualClock,
)
from beatoven.output_module.midi_port import MidiPortTransport, SimulatedPortDevice  # noqa: E402
from beatoven.output_module.tests.test_output_module import stream  # noqa: E402


@pytest.fixture
def port_device():
    try:
        dev = SimulatedPortDevice(name=f"OM Sim {time.monotonic_ns() % 100000}")
    except Exception as exc:  # no MIDI backend on this machine
        pytest.skip(f"no virtual MIDI ports: {exc}")
    time.sleep(0.2)  # let the OS publish the ports
    yield dev
    dev.close()


def _grant(tmp_path):
    f = tmp_path / "grant.json"
    f.write_text(json.dumps({"schema": "beatoven.hardware_lane_grant.v1", "granted_by": "test (virtual port only)",
                             "granted_at": "2026-11-12T00:00:00+00:00", "scope": ["output_module"]}))
    return HardwareLaneGrant.load(f)


def test_at027_real_midi_port_needs_a_grant(port_device):
    transport = MidiPortTransport(port_device.host_to_device, port_device.device_to_host)
    driver = OutputModuleDriver(transport)
    assert driver.connect() is State.SAFE_IDLE and "hardware_control_allowed is false" in driver.reject_reason
    time.sleep(0.05)
    assert port_device.device.lifecycle.state is State.DISCONNECTED
    transport.close()


def test_at028_stream_over_the_os_midi_stack_matches_the_simulated_trace(port_device, tmp_path):
    clock = VirtualClock(1_000_000)
    reference = SimulatedOutputModule()
    ref_driver = OutputModuleDriver(LoopbackTransport(reference, clock), clock)
    ref_driver.connect()
    assert ref_driver.play(stream()).ok

    transport = MidiPortTransport(port_device.host_to_device, port_device.device_to_host)
    driver = OutputModuleDriver(transport, grant=_grant(tmp_path), lookahead_us=150_000, lead_us=150_000)
    assert driver.connect() is State.SYNCED
    report = driver.play(stream())
    transport.close()
    assert report.ok and report.played_hash_ok, report
    assert port_device.device.trace_csv() == reference.trace_csv()
