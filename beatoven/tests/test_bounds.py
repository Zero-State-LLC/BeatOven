from pathlib import Path
import json

from beatoven.engine.render import render_pack


def _load_example() -> dict:
    path = Path("examples/example_input.oracle_signal_layer.v2.json")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_midi_bounds():
    oracle_v2 = _load_example()
    pack = render_pack(oracle_v2, overlays={}, seed=1337, daw="ABLETON")
    tempo = pack["midi"]["tempo_bpm"]
    assert 40 <= tempo <= 220

    tracks = pack["midi"]["tracks"]
    assert len(tracks) >= 1
    for track in tracks:
        assert 1 <= track["midi_channel"] <= 16
        for lane in track["cc_lanes"]:
            assert 0 <= lane["cc"] <= 127
            for point in lane["points"]:
                assert 0 <= point["v"] <= 127
