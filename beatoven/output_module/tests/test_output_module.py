"""Acceptance tests for specs/001-output-module. Test IDs (AT-###) match spec.md."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from beatoven.engine.render import render_pack
from beatoven.output_module import (
    Channel, ChannelKind, ContractError, HardwareLaneDenied, HardwareLaneGrant, IllegalTransition,
    Lifecycle, LoopbackTransport, LossReason, Op, OutputEvent, OutputModuleDriver, OutputStream,
    SimulatedOutputModule, State, VirtualClock, from_audio_control_frames, from_cv_gate_map,
    from_midi_event_stream, from_pack, from_resonance_frame, reference_descriptor,
)
from beatoven.output_module import lifecycle as lc
from beatoven.output_module.adapters import note_to_uv
from beatoven.output_module.wire import Frame, Msg, WireError, pack7, unpack7

ORACLE = {
    "vector_mix": {"ritual_density": 0.6, "meme_velocity": 0.7, "nostalgia": 0.3, "symbolic_modulator": "EMBER"},
    "kairos": {"axis_of_fate": "EXPAND", "framebreaker": "TIMEBOX", "continuum_binder": "THREAD"},
}


def pack(seed=7):
    return render_pack(ORACLE, {}, seed, "ableton")


def stream(seed=7):
    return from_pack(pack(seed), time_unit="beats")


def rig(**kw):
    clock = VirtualClock(1_000_000)
    device = SimulatedOutputModule(clock_offset_us=kw.pop("offset", 123_456_789))
    transport = LoopbackTransport(device, clock)
    return clock, device, transport, OutputModuleDriver(transport, clock, **kw)


# ---- contract (FR-001..FR-004) -------------------------------------------------

def test_at001_same_pack_gives_byte_identical_stream():
    a, b = stream(), stream()
    assert a.canonical_bytes() == b.canonical_bytes() and a.stream_id == b.stream_id
    assert stream(8).stream_id != a.stream_id


def test_at002_every_value_has_an_explicit_unit_and_pitch_is_1v_per_octave():
    assert note_to_uv(12, 12) == 0 and note_to_uv(24, 12) == 1_000_000 and note_to_uv(72, 12) == 5_000_000
    assert note_to_uv(13, 12) == 83_333
    s = stream()
    ops = {e.op for e in s.events}
    assert {Op.SET_UV, Op.GATE_ON, Op.GATE_OFF, Op.PULSE, Op.CLOCK_PERIOD} <= ops
    assert all(isinstance(e.t_us, int) and isinstance(e.value, int) for e in s.events)


def test_at003_json_round_trip_and_tamper_detection():
    s = stream()
    d = json.loads(json.dumps(s.to_dict()))
    assert OutputStream.from_dict(d).stream_id == s.stream_id
    d["events"][3]["t_us"] += 1
    with pytest.raises(ContractError):
        OutputStream.from_dict(d)


@pytest.mark.parametrize("event", [
    OutputEvent(0, Channel(ChannelKind.GATE, 0), Op.SET_UV, 1),
    OutputEvent(0, Channel(ChannelKind.GATE, 0), Op.PULSE, 999),
    OutputEvent(-1, Channel(ChannelKind.GATE, 0), Op.GATE_ON),
    OutputEvent(0, Channel(ChannelKind.PITCH_CV, 0), Op.GATE_ON),
])
def test_at004_invalid_events_are_rejected(event):
    with pytest.raises(ContractError):
        OutputStream.build([event], source_contract="t", source_hash="0")


def test_at005_stream_schema_validates_emitted_json():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((Path(__file__).parents[2] / "schemas" / "beatoven.output_stream.v1.schema.json").read_text())
    jsonschema.validate(stream().to_dict(), schema)


# ---- adapters (FR-005..FR-009) ---------------------------------------------------

def test_at006_pack_adapter_requires_time_unit_and_reports_what_it_cannot_map():
    with pytest.raises(TypeError):
        from_pack(pack())
    with pytest.raises(ContractError):
        from_pack(pack(), time_unit="ticks")
    notes = "\n".join(stream().notes)
    assert "CLOCK lane points" in notes and "UNROUTED: track role TEXTURE" in notes


def test_at007_pack_public_shape_is_untouched():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((Path(__file__).parents[2] / "schemas" / "beatoven.pack.v0.schema.json").read_text())
    p = pack()
    before = json.dumps(p, sort_keys=True)
    from_pack(p, time_unit="beats")
    assert json.dumps(p, sort_keys=True) == before
    jsonschema.validate(p, schema)


@dataclass
class _Metrics:
    complexity: float = 0.1
    emotional_intensity: float = 0.2
    groove: float = 0.3
    energy: float = 0.4
    density: float = 0.5
    swing: float = 0.6
    brightness: float = 0.7
    tension: float = 0.8


@dataclass
class _Rhythm:
    bpm: float = 120.0
    meter: Tuple[int, int] = (4, 4)
    kick: Optional[List[float]] = None
    snare: Optional[List[float]] = None
    hat: Optional[List[float]] = None
    perc: Optional[List[float]] = None


@dataclass
class _Frame:
    id: str = "f1"
    provenance_hash: str = "ab" * 32
    metrics: Optional[_Metrics] = None
    rhythm: Optional[_Rhythm] = None


def test_at008_resonance_frame_adapter():
    frame = _Frame(metrics=_Metrics(), rhythm=_Rhythm(kick=[1, 0, 0, 0, 1, 0, 0, 0], hat=[0.4] * 8))
    with pytest.raises(TypeError):
        from_resonance_frame(frame, bars=1)
    s = from_resonance_frame(frame, bars=2, step_threshold=0.5)
    kicks = [e.t_us for e in s.events if e.channel.name == "GATE:0"]
    assert kicks == [0, 1_000_000, 2_000_000, 3_000_000]
    assert not [e for e in s.events if e.channel.name == "GATE:2"]
    energy = [e for e in s.events if e.channel.name == "MOD_CV:0"][0]
    assert energy.value == 2_000_000  # 0.4 of 0..5 V
    assert any("groove" in n for n in s.notes) and any("swing" in n for n in s.notes)


def test_at009_audio_control_frame_and_cv_gate_map_adapters():
    frames = [{"window_utc": f"w{i}", "tempo_bpm": 120.0, "rhythm_density": 0.5, "spectral_centroid": 0.2,
               "harmonic_tension": 1.0, "modulation_rate": 0.0, "silence_probability": 0.1} for i in range(2)]
    with pytest.raises(TypeError):
        from_audio_control_frames(frames)
    s = from_audio_control_frames(frames, window_us=2_000_000)
    assert [e.value for e in s.events if e.channel.kind is ChannelKind.CLOCK] == [125_000, 0]
    assert [e.value for e in s.events if e.channel.name == "MOD_CV:2"] == [5_000_000, 5_000_000]
    g = from_cv_gate_map({"clock_hz": 2.0, "gate_pattern": "1010"})
    assert [e.t_us for e in g.events if e.op is Op.PULSE] == [0, 1_000_000]
    with pytest.raises(ContractError):
        from_cv_gate_map({"clock_hz": 2.0, "gate_pattern": "10x0"})


def test_at010_midi_event_stream_adapter():
    src = {"schema_version": "MIDIEventStream.v1", "stream_id": "sha256:x", "sync_mode": "absolute_tick",
           "events": [{"t": 0, "status": 0x91, "data1": 36, "data2": 100},
                      {"t": 480, "status": 0x81, "data1": 36, "data2": 0},
                      {"t": 0, "status": 0x90, "data1": 36, "data2": 100},
                      {"t": 10, "status": 0x80, "data1": 36, "data2": 0}],
           "transport": {"target": "hardware_synth", "command_rate_budget": 0}}
    with pytest.raises(ContractError):
        from_midi_event_stream(src)
    s = from_midi_event_stream(src, ppq=480, tempo_bpm=120)
    assert OutputEvent(0, Channel(ChannelKind.PITCH_CV, 0), Op.SET_UV, 2_000_000) in s.events
    assert OutputEvent(500_000, Channel(ChannelKind.GATE, 1), Op.GATE_OFF) in s.events
    assert OutputEvent(0, Channel(ChannelKind.GATE, 0), Op.PULSE, 5_000) in s.events


def test_at011_overlapping_notes_are_cut_one_ms_before_the_next():
    s = stream()  # this Pack has grid 0.5 beat and duration 0.75 beat
    bass = [e for e in s.events if e.channel.name == "GATE:1"]
    for off, on in zip(bass[1::2], bass[2::2]):
        assert off.op is Op.GATE_OFF and on.op is Op.GATE_ON and on.t_us - off.t_us == 1_000


# ---- wire (FR-010, FR-011) -------------------------------------------------------

def test_at012_wire_frames_are_7bit_clean_and_checked():
    body = bytes(range(256))
    assert unpack7(pack7(body)) == body
    raw = Frame(Msg.EVENTS, 5, body).encode()
    assert raw[0] == 0xF0 and raw[-1] == 0xF7 and all(b < 0x80 for b in raw[1:-1])
    assert Frame.decode(raw) == Frame(Msg.EVENTS, 5, body)
    bad = bytearray(raw)
    bad[20] ^= 0x01
    with pytest.raises(WireError):
        Frame.decode(bytes(bad))


def test_at013_ops_lane_kinds_survive_in_the_new_envelope():
    _, device, _, driver = rig()
    driver.connect()
    assert driver.ops("PING") is True
    assert driver.ops("LOAD_PRESET", {"preset_id": "p1"}) is False  # the reference device has no presets
    assert [m["kind"] for m in device.ops_log] == ["PING", "LOAD_PRESET"]
    assert set(device.ops_log[1]) == {"kind", "nonce", "payload"}


# ---- lifecycle (FR-012..FR-016) ----------------------------------------------------

def test_at014_transitions_table_is_complete_and_illegal_moves_raise():
    assert lc.INITIAL is State.DISCONNECTED and lc.FINAL == (State.DISCONNECTED,)
    table = lc.as_table()
    assert len(table) == 14 and set(table[0]) == {"from", "event", "guard", "to", "effect"}
    illegal = lc.illegal_transitions()
    assert len(illegal) == len(State) * len(lc.Event) - 14
    for state, event in illegal:
        machine = Lifecycle()
        machine.state = state
        with pytest.raises(IllegalTransition):
            machine.fire(event)
    assert (State.TIMING_LOST, lc.Event.STREAM_BEGIN) in illegal
    assert (State.SAFE_IDLE, lc.Event.STREAM_BEGIN) in illegal
    assert (State.DISCONNECTED, lc.Event.STREAM_BEGIN) in illegal


def test_at015_happy_path_walks_the_lifecycle():
    _, device, _, driver = rig()
    assert driver.lifecycle.state is State.DISCONNECTED
    assert driver.connect() is State.SYNCED and driver.offset_us == 123_456_789
    report = driver.play(stream())
    assert report.ok and report.played_hash_ok and report.final_state is State.SYNCED
    assert device.lifecycle.state is State.SYNCED
    driver.close()
    assert driver.lifecycle.state is State.DISCONNECTED and device.lifecycle.state is State.DISCONNECTED


def test_at016_seed_replay_gives_identical_jack_traces():
    traces = []
    for offset in (0, 987_654_321):  # device clock epoch must not matter
        _, device, _, driver = rig(offset=offset)
        driver.connect()
        assert driver.play(stream()).ok
        traces.append(device.trace_csv())
    assert traces[0] == traces[1] and traces[0].count("\n") > 50


def test_at017_gates_and_clock_are_low_after_the_stream_ends():
    _, device, _, driver = rig()
    driver.connect()
    driver.play(stream())
    last = {}
    for _t, jack, kind, value in device.trace:
        if kind == "LEVEL":
            last[jack] = value
    assert last and set(last.values()) == {0}


@pytest.mark.parametrize("fault,reason", [
    ("drop", LossReason.SEQUENCE_GAP),
    ("late", LossReason.LATE_EVENT),
    ("silent", LossReason.KEEPALIVE_TIMEOUT),
])
def test_at018_timing_loss_fails_closed(fault, reason):
    clock, device, transport, driver = rig()
    driver.connect()
    s = stream()
    original = transport.send
    count = {"n": 0}

    def faulty(data):
        count["n"] += 1  # send 1 is STREAM_BEGIN
        if fault == "drop" and count["n"] == 3:
            return
        if fault == "silent" and count["n"] >= 3:
            return
        if fault == "late" and count["n"] >= 2:
            transport.delay_us = 400_000
        original(data)
    transport.send = faulty
    report = driver.play(s)
    assert not report.ok and report.loss_reason is reason
    assert report.final_state is State.SAFE_IDLE and device.lifecycle.state is State.SAFE_IDLE
    lost_at = max(t for t, _j, k, _v in device.trace if k == "SLEW_TO_UV") if any(
        k == "SLEW_TO_UV" for *_x, k, _v in device.trace) else None
    levels = {}
    for _t, jack, kind, value in device.trace:
        if kind == "LEVEL":
            levels[jack] = value
    assert set(levels.values()) <= {0}
    after = [e for e in device.trace if lost_at is not None and e[0] > lost_at]
    assert after == []  # nothing plays after the fail-closed moment


def test_at019_no_automatic_resume_after_timing_loss():
    clock, device, transport, driver = rig()
    driver.connect()
    transport.drop_next = 0
    original = transport.send
    sends = []

    def drop_third(data):
        sends.append(1)
        if len(sends) != 3:
            original(data)
    transport.send = drop_third
    assert driver.play(stream()).final_state is State.SAFE_IDLE
    transport.send = original
    with pytest.raises(IllegalTransition):
        driver.play(stream())
    assert driver.resync() is State.SYNCED
    assert driver.play(stream()).ok


def test_at020_stream_that_exceeds_the_device_range_is_refused_before_sending():
    _, device, _, driver = rig()
    driver.connect()
    too_high = OutputStream.build(
        [OutputEvent(0, Channel(ChannelKind.PITCH_CV, 0), Op.SET_UV, 11_000_000)],
        source_contract="t", source_hash="0")
    with pytest.raises(ContractError):
        driver.play(too_high)
    assert driver.lifecycle.state is State.SYNCED and device.trace == []


# ---- authority (FR-017) --------------------------------------------------------------

def test_at021_hardware_lane_is_denied_without_an_operator_grant(tmp_path):
    clock, device, transport, driver = rig()
    transport.simulated = False
    assert driver.connect() is State.SAFE_IDLE
    assert "hardware_control_allowed is false" in driver.reject_reason
    assert device.lifecycle.state is State.DISCONNECTED and device.trace == []

    grant_file = tmp_path / "grant.json"
    grant_file.write_text(json.dumps({
        "schema": "beatoven.hardware_lane_grant.v1", "granted_by": "operator",
        "granted_at": "2026-11-11T00:00:00+00:00", "scope": ["output_module"]}))
    clock, device, transport, driver = rig(grant=HardwareLaneGrant.load(grant_file))
    transport.simulated = False
    assert driver.connect() is State.SYNCED

    grant_file.write_text(json.dumps({
        "schema": "beatoven.hardware_lane_grant.v1", "granted_by": "operator",
        "granted_at": "2026-11-11T00:00:00+00:00", "scope": ["something_else"]}))
    with pytest.raises(HardwareLaneDenied):
        HardwareLaneGrant.load(grant_file).check()


def test_at022_dac_quantization_is_integer_and_within_half_an_lsb():
    spec = reference_descriptor().spec(Channel(ChannelKind.PITCH_CV, 0))
    lsb = 10_000_000 / 65535
    for note in range(12, 73):
        uv = note_to_uv(note, 12)
        code, out = spec.quantize(uv)
        assert 0 <= code <= 65535 and abs(out - uv) <= lsb / 2 + 1
