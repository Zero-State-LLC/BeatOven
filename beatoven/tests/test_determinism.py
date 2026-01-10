from pathlib import Path
import json

from beatoven.engine.hashing import hash_pack
from beatoven.engine.render import render_pack


def _load_example() -> dict:
    path = Path("examples/example_input.oracle_signal_layer.v2.json")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_determinism_invariance():
    oracle_v2 = _load_example()
    seed = 1337
    first_pack = render_pack(oracle_v2, overlays={}, seed=seed, daw="ABLETON")
    first_hash = hash_pack(first_pack)
    for _ in range(12):
        pack = render_pack(oracle_v2, overlays={}, seed=seed, daw="ABLETON")
        assert hash_pack(pack) == first_hash
