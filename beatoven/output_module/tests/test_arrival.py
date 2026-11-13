"""Tests for the play-on-arrival mapping proposed in docs/adr/0007. Pure: no device, no grant."""

from beatoven.output_module import arrival
from beatoven.output_module.arrival import ArrivalMapper
from beatoven.output_module.contract import _validate_event


def ev(events):
    return [(e.t_us, e.channel.name, e.op.name, e.value) for e in events]


def test_the_mode_is_labelled_non_deterministic():
    assert arrival.LABEL == "NON_DETERMINISTIC"


def test_note_on_sets_pitch_then_raises_the_gate_at_arrival_time():
    m = ArrivalMapper()
    assert ev(m.feed(bytes([0x90, 60, 100]), 1_000)) == [
        (1_000, "PITCH_CV:0", "SET_UV", 4_000_000),   # note 12 is 0 V, so note 60 is 4 V
        (1_000, "GATE:0", "GATE_ON", 0),
    ]
    assert ev(m.feed(bytes([0x80, 60, 0]), 2_000)) == [(2_000, "GATE:0", "GATE_OFF", 0)]


def test_last_note_wins_and_release_returns_to_the_held_note():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100]), 0)
    assert ev(m.feed(bytes([0x90, 72, 100]), 10)) == [(10, "PITCH_CV:0", "SET_UV", 5_000_000)]
    assert ev(m.feed(bytes([0x80, 72, 0]), 20)) == [(20, "PITCH_CV:0", "SET_UV", 4_000_000)]
    assert ev(m.feed(bytes([0x90, 60, 0]), 30)) == [(30, "GATE:0", "GATE_OFF", 0)]  # velocity 0 is note-off


def test_releasing_a_note_under_the_newest_changes_nothing():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100, 72, 100]), 0)   # running status
    assert m.feed(bytes([0x80, 60, 0]), 10) == []


def test_channel_two_drives_the_second_voice():
    m = ArrivalMapper()
    assert ev(m.feed(bytes([0x91, 24, 1]), 5)) == [(5, "PITCH_CV:1", "SET_UV", 1_000_000), (5, "GATE:1", "GATE_ON", 0)]


def test_notes_the_jack_cannot_produce_are_ignored():
    m = ArrivalMapper()
    assert m.feed(bytes([0x90, 11, 100]), 0) == []   # below 0 V
    assert m.feed(bytes([0x80, 11, 0]), 1) == []
    assert m.feed(bytes([0x92, 60, 100]), 2) == []   # channel 3 has no voice


def test_pitch_bend_moves_a_held_note_by_up_to_two_semitones():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100]), 0)
    assert ev(m.feed(bytes([0xE0, 0x00, 0x00]), 10)) == [(10, "PITCH_CV:0", "SET_UV", 3_833_333)]
    assert ev(m.feed(bytes([0xE0, 0x00, 0x40]), 20)) == [(20, "PITCH_CV:0", "SET_UV", 4_000_000)]
    m.feed(bytes([0x80, 60, 0]), 30)
    assert m.feed(bytes([0xE0, 0x00, 0x00]), 40) == []   # no held note: nothing to move


def test_controllers_map_to_mod_cv_from_zero_to_five_volts():
    m = ArrivalMapper()
    assert ev(m.feed(bytes([0xB0, 1, 127, 2, 0, 19, 64]), 7)) == [
        (7, "MOD_CV:0", "SET_UV", 5_000_000),
        (7, "MOD_CV:1", "SET_UV", 0),
        (7, "MOD_CV:5", "SET_UV", 2_519_685),
    ]
    assert m.feed(bytes([0xB0, 7, 100]), 8) == []        # unmapped controller
    assert m.feed(bytes([0xB1, 1, 100]), 9) == []        # controllers are read on channel 1 only


def test_channel_ten_notes_fire_triggers():
    m = ArrivalMapper()
    assert ev(m.feed(bytes([0x99, 36, 100, 38, 1, 40, 100]), 3)) == [
        (3, "GATE:2", "PULSE", 5_000), (3, "GATE:3", "PULSE", 5_000),
    ]
    assert m.feed(bytes([0x89, 36, 0]), 4) == []


def test_clock_start_and_stop():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100]), 0)
    assert ev(m.feed(bytes([0xFA]), 100)) == [(100, "RESET:0", "PULSE", 5_000)]
    assert ev(m.feed(bytes([0xF8]), 100)) == [(100, "CLOCK:0", "PULSE", 5_000)]
    assert ev(m.feed(bytes([0xF8]), 20_933)) == [(20_933, "CLOCK:0", "PULSE", 5_000)]   # 120 BPM
    assert ev(m.feed(bytes([0xF8]), 26_933)) == [(26_933, "CLOCK:0", "PULSE", 3_000)]   # fast: half the interval
    assert ev(m.feed(bytes([0xF8]), 27_433)) == [(27_433, "CLOCK:0", "PULSE", 1_000)]   # never under 1 ms
    assert ev(m.feed(bytes([0xFC]), 30_000)) == [(30_000, "GATE:0", "GATE_OFF", 0)]


def test_all_notes_off_drops_the_gate_once():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100, 64, 100]), 0)
    assert ev(m.feed(bytes([0xB0, 123, 0]), 5)) == [(5, "GATE:0", "GATE_OFF", 0)]
    assert m.feed(bytes([0xB0, 123, 0]), 6) == []
    assert m.feed(bytes([0x80, 64, 0]), 7) == []


def test_real_time_bytes_inside_a_message_do_not_break_it():
    m = ArrivalMapper()
    assert ev(m.feed(bytes([0x90, 60, 0xF8, 100]), 9)) == [
        (9, "CLOCK:0", "PULSE", 5_000), (9, "PITCH_CV:0", "SET_UV", 4_000_000), (9, "GATE:0", "GATE_ON", 0),
    ]


def test_sysex_and_system_common_are_skipped():
    m = ArrivalMapper()
    # A status byte ends an unterminated SysEx, and the message after it plays.
    assert ev(m.feed(bytes([0xF0, 0x7D, 0x42, 0x4F, 0x90, 60, 100]), 0))[1] == (0, "GATE:0", "GATE_ON", 0)
    m = ArrivalMapper()
    assert m.feed(bytes([0xF0, 0x7D, 60, 100, 0xF7, 60, 100]), 0) == []      # data after F7 has no status
    assert m.feed(bytes([0xF2, 0x10, 0x20, 60, 100]), 1) == []               # song position, then stray data
    assert ev(m.feed(bytes([0xC0, 5, 0xD0, 9, 0x90, 60, 100]), 2))[1] == (2, "GATE:0", "GATE_ON", 0)


def test_a_message_split_across_feeds_plays_when_it_completes():
    m = ArrivalMapper()
    assert m.feed(bytes([0x90, 60]), 10) == []
    assert ev(m.feed(bytes([100]), 900))[0] == (900, "PITCH_CV:0", "SET_UV", 4_000_000)


def test_active_sensing_loss_drops_gates_only_if_it_was_ever_seen():
    m = ArrivalMapper()
    m.feed(bytes([0x90, 60, 100]), 0)
    assert m.tick(10_000_000) == []                      # never saw FE: the note stays held
    m.feed(bytes([0xFE]), 10_000_000)
    assert m.tick(10_299_999) == []
    assert ev(m.tick(10_300_000)) == [(10_300_000, "GATE:0", "GATE_OFF", 0)]
    assert m.tick(11_000_000) == []


def test_every_event_is_legal_under_the_contract():
    m = ArrivalMapper()
    stream = bytes([0xFA, 0x90, 60, 100, 0xF8, 0xE0, 0, 0, 0xB0, 1, 64, 0x99, 36, 9, 0x91, 127, 1, 0xF8, 0xFC])
    events = m.feed(stream, 123)
    assert len(events) == 12
    for e in events:
        _validate_event(e)
        assert m.descriptor.spec(e.channel) is not None
