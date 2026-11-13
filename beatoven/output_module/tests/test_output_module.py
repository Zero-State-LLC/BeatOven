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
    # Operator decisions B1-B3 (2026-11-12): bars, and a clock from tempo at 24 per quarter note.
    assert from_pack(pack()).stream_id == from_pack(pack(), time_unit="bars", clock_ppqn=24).stream_id
    assert from_pack(pack()).stream_id != from_pack(pack(), time_unit="beats").stream_id
    bpm = pack()["midi"]["tempo_bpm"]
    clock = [e.value for e in from_pack(pack()).events if e.channel.kind is ChannelKind.CLOCK]
    assert clock == [round(60_000_000 / (bpm * 24)), 0]
    assert not [e for e in from_pack(pack(), clock_ppqn=None).events if e.channel.kind is ChannelKind.CLOCK]
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
    # Operator decision B10: a step value is a velocity and fires above 0.
    by_default = from_resonance_frame(frame, bars=1)
    assert len([e for e in by_default.events if e.channel.name == "GATE:2"]) == 8
    assert len([e for e in by_default.events if e.channel.name == "GATE:0"]) == 2
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
    assert [e.value for e in s.events if e.channel.kind is ChannelKind.CLOCK] == [20_833, 0]
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
        is_events = data[5] == 0x04
        count["events"] = count.get("events", 0) + is_events
        if fault == "drop" and is_events and count["events"] == 2:
            return
        if fault == "silent" and count["n"] >= 3:
            return
        if fault == "late" and count["n"] >= 2:
            transport.delay_us = 200_000  # past the look-ahead, inside the 300 ms keepalive
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

    def drop_third(data):  # drops the second EVENTS frame
        sends.append(data[5] == 0x04)
        if not (data[5] == 0x04 and sum(sends) == 2):
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


# ---- device-side checks (FR-003, FR-014): the device does not trust the host ---------

def _streaming_device():
    import struct
    device = SimulatedOutputModule()
    device.feed(Frame(Msg.HELLO, 0, b"").encode(), 0)
    device.feed(Frame(Msg.SYNC, 1, struct.pack(">Q", 0)).encode(), 0)
    return device, struct


def test_at023_malformed_bodies_are_refused_not_raised():
    device, struct = _streaming_device()
    device.feed(Frame(Msg.STREAM_BEGIN, 2, b"short").encode(), 0)
    device.feed(Frame(Msg.OPS, 3, b"\xff\xff").encode(), 0)
    device.feed(Frame(Msg.OPS, 4, b"\x01").encode(), 0)
    assert device.lifecycle.state is State.SYNCED and device.trace == []
    device.feed(Frame(Msg.STREAM_BEGIN, 5, struct.pack(">32sIQI", b"x" * 32, 1, 50_000, 0)).encode(), 0)
    assert device.lifecycle.state is State.SYNCED  # zero-width clock pulse refused


@pytest.mark.parametrize("event,count", [
    (OutputEvent(0, Channel(ChannelKind.GATE, 0), Op.SET_UV, 1), 1),          # op not allowed on the kind
    (OutputEvent(0, Channel(ChannelKind.PITCH_CV, 9), Op.SET_UV, 1), 1),      # channel the device lacks
    (OutputEvent(0, Channel(ChannelKind.PITCH_CV, 0), Op.SET_UV, -5), 1),     # below the channel range
    (OutputEvent(0, Channel(ChannelKind.GATE, 0), Op.GATE_ON), 0),            # more events than announced
])
def test_at024_device_fails_closed_on_events_it_cannot_play(event, count):
    from beatoven.output_module.wire import events_body
    device, struct = _streaming_device()
    device.feed(Frame(Msg.STREAM_BEGIN, 2, struct.pack(">32sIQI", b"x" * 32, max(count, 1) if count else 1, 50_000, 5_000)).encode(), 0)
    events = [event] if count else [event, OutputEvent(1, Channel(ChannelKind.GATE, 0), Op.GATE_OFF)]
    device.feed(Frame(Msg.EVENTS, 3, events_body(0, events)).encode(), 0)
    assert device.lifecycle.state is State.TIMING_LOST and device.loss_reason is LossReason.INTEGRITY
    device.advance(1_000_000)
    assert device.lifecycle.state is State.SAFE_IDLE and not [e for e in device.trace if e[2] == "CV_UV"]


# ---- one-way fallback link (FR-026) -------------------------------------------------

def test_at025_one_way_link_plays_the_same_jack_trace_unconfirmed():
    from beatoven.output_module import OneWayLoopbackTransport
    _, two_way_device, _, two_way = rig()
    two_way.connect()
    assert two_way.play(stream()).ok

    clock = VirtualClock(1_000_000)
    device = SimulatedOutputModule(clock_offset_us=55_555)
    driver = OutputModuleDriver(OneWayLoopbackTransport(device, clock), clock)
    report = driver.play_one_way(stream(), reference_descriptor())
    device.advance(clock.now_us() + 1_000_000)
    assert report.ok and report.confirmed is False and report.played_hash_ok is False
    assert device.lifecycle.state is State.SYNCED and device.loss_reason is None
    assert device.trace_csv() == two_way_device.trace_csv()


def test_at026_one_way_link_too_slow_for_the_stream_fails_closed():
    from beatoven.output_module import OneWayLoopbackTransport
    clock = VirtualClock(1_000_000)
    device = SimulatedOutputModule()
    driver = OutputModuleDriver(OneWayLoopbackTransport(device, clock, byte_us=3_000), clock)
    report = driver.play_one_way(stream(), reference_descriptor())
    device.advance(clock.now_us() + 600_000_000)  # past everything the slow line still carried
    device.advance(clock.now_us() + 601_000_000)
    assert report.confirmed is False
    moves = [(a, e) for a, e, _b in device.lifecycle.history]
    assert (State.STREAMING, lc.Event.TIMING_LOSS) in moves and (State.STREAMING, lc.Event.STREAM_END) not in moves
    assert device.lifecycle.state is not State.STREAMING
    levels = {}
    for _t, jack, kind, value in device.trace:
        if kind == "LEVEL":
            levels[jack] = value
    assert set(levels.values()) <= {0}


# ---- clock drift (FR-013) ------------------------------------------------------------

@pytest.mark.parametrize("ppm", [-40_000, 40_000])
def test_at029_host_follows_a_drifting_device_clock(ppm):
    """A crystal error far beyond any real part; uncorrected, it would exceed the look-ahead."""
    _, reference, _, ref_driver = rig()
    ref_driver.connect()
    assert ref_driver.play(stream()).ok

    clock = VirtualClock(1_000_000)
    device = SimulatedOutputModule(clock_offset_us=777, clock_ppm=ppm)
    driver = OutputModuleDriver(LoopbackTransport(device, clock), clock, sync_interval_us=50_000)
    driver.connect()
    report = driver.play(stream())
    assert report.ok and report.played_hash_ok, report
    assert device.trace_csv() == reference.trace_csv()  # the device's own timeline is unchanged


# ---- Pack v1 (ADR 0002) and deterministic ResonanceFrame (ADR 0003) ------------------

def test_pack_v1_states_its_units_and_embeds_the_stream_it_compiles_to():
    jsonschema = pytest.importorskip("jsonschema")
    v0 = render_pack(ORACLE, {}, 7, "ableton")
    v1 = render_pack(ORACLE, {}, 7, "ableton", schema_version="v1")
    assert v0 == pack(7) and "output_stream" not in v0 and "schema" not in v0["meta"]  # v0 untouched
    schemas = Path(__file__).parents[2] / "schemas"
    jsonschema.validate(v1, json.loads((schemas / "beatoven.pack.v1.schema.json").read_text()))
    jsonschema.validate(v0, json.loads((schemas / "beatoven.pack.v0.schema.json").read_text()))
    assert v1["midi"]["time_unit"] == "bars" and v1["midi"]["clock_ppqn"] == 24 and "cv" not in v1
    assert v1 == render_pack(ORACLE, {}, 7, "ableton", schema_version="v1")
    embedded = OutputStream.from_dict(v1["output_stream"])
    recompiled = from_pack(v1)
    assert recompiled.stream_id == embedded.stream_id
    assert v1["provenance"]["output_hashes"]["output_stream"] == v1["output_stream"]["stream_id"] == "sha256:" + embedded.stream_id
    assert recompiled.to_dict()["source"]["contract"] == "beatoven.pack.v1"
    assert from_pack(v1, time_unit="beats").stream_id != embedded.stream_id  # the override still works
    with pytest.raises(ValueError):
        render_pack(ORACLE, {}, 7, "ableton", schema_version="v2")


def test_resonance_frame_from_source_is_deterministic():
    from beatoven.dspcoffee_bridge.schema import ResonanceFrame
    a = ResonanceFrame.from_source("text", id="f1", ts_ms=1000)
    b = ResonanceFrame.from_source("text", id="f1", ts_ms=1000)
    assert a == b and a.provenance_hash == b.provenance_hash
    with pytest.raises(TypeError):
        ResonanceFrame.from_source("text")
    assert ResonanceFrame.new("text").id != ResonanceFrame.new("text").id


# ---- calibration and CLOCK IN (FR-028..FR-030; ADRs 0005, 0006) -------------------

PITCH0, MOD0, GATE0 = 0x00, 0x10, 0x20


def test_at030_calibration_write_read_and_revert_never_change_the_jack_trace():
    from beatoven.output_module.sim import calibrated_code

    clock, device, _, driver = rig()
    driver.connect()
    assert driver.descriptor.calibration == "identity"
    assert driver.cal_read()["state"] == "identity"
    assert driver.cal_revert() is False                       # nothing to return to

    first = [{"channel": PITCH0, "gain_ppm": 1_000, "offset_lsb16": -32}]
    second = [{"channel": PITCH0, "gain_ppm": -500, "offset_lsb16": 16}, {"channel": MOD0, "gain_ppm": 7, "offset_lsb16": 0}]
    assert driver.cal_write(first) and driver.cal_write(second)
    read = driver.cal_read()
    assert read["state"] == "stored" and len(read["entries"]) == 8
    assert read["entries"][0] == second[0] and read["entries"][2] == second[1]
    assert driver.cal_revert() and driver.cal_read()["entries"][0] == first[0]

    s = stream()
    report = driver.play(s)
    assert report.ok and report.played_hash_ok
    _, plain, _, plain_driver = rig()
    plain_driver.connect()
    plain_driver.play(s)
    assert device.trace_hash() == plain.trace_hash()           # calibration moves DAC codes only
    assert device.dac_codes["PITCH_CV:0"] != plain.dac_codes["PITCH_CV:0"]
    assert device.dac_codes["PITCH_CV:1"] == plain.dac_codes["PITCH_CV:1"]
    # Same integer arithmetic as the firmware core (kc_calib_apply).
    assert calibrated_code(32768, 1_000, -32) == 32799 and calibrated_code(65535, 20_000, 1_600) == 65535
    assert calibrated_code(0, 0, -16) == 0 and calibrated_code(1000, 0, 8) == 1001

    device.fail_calibration_storage()                           # both stored records fail their check
    assert driver.cal_read() == {"state": "identity", "entries": [
        {"channel": ch, "gain_ppm": 0, "offset_lsb16": 0} for ch in (0, 1, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15)]}


@pytest.mark.parametrize("entries", [
    [],
    [{"channel": PITCH0, "gain_ppm": 20_001, "offset_lsb16": 0}],
    [{"channel": PITCH0, "gain_ppm": 0, "offset_lsb16": -1_601}],
    [{"channel": GATE0, "gain_ppm": 0, "offset_lsb16": 0}],          # gates have no calibration
    [{"channel": 0x02, "gain_ppm": 0, "offset_lsb16": 0}],           # no such channel on this device
    [{"channel": 0x7F, "gain_ppm": 0, "offset_lsb16": 0}],
    [{"channel": PITCH0, "gain_ppm": 1.5, "offset_lsb16": 0}],
    [{"channel": PITCH0, "gain_ppm": True, "offset_lsb16": 0}],
    [{"channel": PITCH0, "gain_ppm": 1, "offset_lsb16": 0}, {"channel": PITCH0, "gain_ppm": 2, "offset_lsb16": 0}],
    [{"channel": MOD0, "gain_ppm": 5, "offset_lsb16": 5}, {"channel": PITCH0}],   # one bad entry refuses all
    "not a list",
])
def test_at031_calibration_write_is_all_or_nothing_and_only_while_synced(entries):
    _, device, _, driver = rig()
    driver.connect()
    good = [{"channel": PITCH0, "gain_ppm": 100, "offset_lsb16": 1}]
    assert driver.cal_write(good)
    assert driver.cal_write(entries) is False
    assert driver.cal_read()["entries"][0] == good[0]           # the stored record is untouched

    device.feed(Frame(Msg.ABORT, 0, b"").encode(), 0)
    device.lifecycle.state = State.STREAMING                    # any state but SYNCED refuses all three
    assert driver.cal_read() is None and driver.cal_write(good) is False and driver.cal_revert() is False


def test_at032_changing_calibration_on_hardware_needs_its_own_expiring_grant():
    def grant(scope, expires_at=None):
        return HardwareLaneGrant("operator", "2026-11-13T00:00:00+00:00", tuple(scope), expires_at)

    entries = [{"channel": PITCH0, "gain_ppm": 1, "offset_lsb16": 1}]
    cases = [
        (grant(["output_module"]), "does not cover scope 'output_module.calibrate'"),
        (grant(["output_module", "output_module.calibrate"]), "must state when it expires"),
        (grant(["output_module", "output_module.calibrate"], "2020-01-01T00:00:00+00:00"), "expired"),
    ]
    for g, why in cases[:2]:
        _, device, transport, driver = rig(grant=g)
        transport.simulated = False
        assert driver.connect() is State.SYNCED
        for call in (lambda: driver.cal_write(entries), driver.cal_revert):
            with pytest.raises(HardwareLaneDenied, match=why):
                call()
        assert [m["kind"] for m in device.ops_log] == []         # nothing was sent
        assert driver.cal_read()["state"] == "identity"          # reading needs no calibration scope
    with pytest.raises(HardwareLaneDenied, match=cases[2][1]):
        cases[2][0].check(scope="output_module.calibrate")

    _, device, transport, driver = rig(grant=grant(["output_module", "output_module.calibrate"], "2999-01-01T00:00:00+00:00"))
    transport.simulated = False
    driver.connect()
    assert driver.cal_write(entries) and driver.cal_read()["state"] == "stored"

    _, _, transport, driver = rig(grant=grant(["output_module.calibrate"], "2999-01-01T00:00:00+00:00"))
    transport.simulated = False
    assert driver.connect() is State.SAFE_IDLE                   # the calibrate scope does not open play


def test_at033_clock_in_is_reported_and_never_changes_playout():
    clock, device, _, driver = rig()
    device.clock_in_edge(clock.now_us())                        # before sync: counted by nobody
    driver.connect()
    assert driver.descriptor.clock_in is True and driver.clock_in is None

    t0 = clock.now_us()
    for i in range(1, 12):                                      # 20 ms apart: 125 BPM at 24 PPQN
        device.clock_in_edge(t0 + i * 20_000)
    clock.sleep_until(t0 + 240_000)
    driver.ops("PING")
    r = driver.clock_in
    assert r.period_us == 20_000 and r.edges == 11 and r.bpm() == 125.0 and r.bpm(4) == 750.0
    assert r.edge_us == t0 + 220_000 + device.clock_offset_us
    reports = [f for f in device_frames(device) if f == Msg.CLOCK_IN]
    assert len(reports) == 3                                    # at most one per 100 ms, not one per edge

    s = stream()
    report = driver.play(s)
    _, plain, _, plain_driver = rig()
    plain_driver.connect()
    plain_driver.play(s)
    assert report.ok and device.trace_csv() == plain.trace_csv()

    clock.sleep_until(t0 + 220_000 + 2_000_000)                 # 2 s with no edge: one final report
    driver.ops("PING")
    assert driver.clock_in.period_us == 0 and driver.clock_in.bpm() is None and driver.clock_in.edges == 11
    assert device_frames(device).count(Msg.CLOCK_IN) == 4

    # A stop that happens while the device may not report is reported once it is SYNCED again.
    device.clock_in_edge(clock.now_us())
    device.clock_in_edge(clock.now_us() + 10_000)
    clock.sleep_until(clock.now_us() + 3_000_000)               # sync timeout first, then the clock stops
    driver.transport.recv()
    clock.sleep_until(clock.now_us() + 100_000)                 # let the slew to Safe Values finish
    driver.transport.recv()
    assert device.lifecycle.state is State.SAFE_IDLE and device_frames(device).count(Msg.CLOCK_IN) == 4
    driver.lifecycle.state = State.SAFE_IDLE
    assert driver.resync() is State.SYNCED
    driver.ops("PING")
    assert driver.clock_in.period_us == 0 and driver.clock_in.edges == 0


def device_frames(device):
    """Types of every frame the device has sent, recorded by wrapping its sender once."""
    return device._sent_types


@pytest.fixture(autouse=True)
def _record_sent_types(monkeypatch):
    original = SimulatedOutputModule._send

    def recording(self, mtype, body):
        self.__dict__.setdefault("_sent_types", []).append(mtype)
        original(self, mtype, body)

    monkeypatch.setattr(SimulatedOutputModule, "_send", recording)


def test_at034_a_host_ignores_device_messages_it_does_not_know():
    _, device, _, driver = rig()
    driver.connect()
    unknown = bytearray(Frame(Msg.STATUS, 1, b"\x00\x00\x00\x00\x00\x00").encode())
    unknown[5] = 0x4F                                           # a type no host knows yet
    device._tx.append(bytes(unknown))
    assert driver.ops("PING") is True
    d = reference_descriptor().to_dict()
    old = {k: v for k, v in d.items() if k not in ("clock_in", "calibration")}
    from beatoven.output_module.contract import Descriptor
    parsed = Descriptor.from_dict(old)                          # a descriptor written before ADRs 0005 and 0006
    assert parsed.clock_in is False and parsed.calibration is None and parsed.to_dict() == old
