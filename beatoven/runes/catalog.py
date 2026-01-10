from typing import Dict


def register() -> Dict[str, dict]:
    return {
        "beatoven.render.v0": {
            "rune_id": "beatoven.render.v0",
            "input_schema": "oracle_signal_layer.v2",
            "output_schema": "beatoven.pack.v0",
            "entrypoint": "beatoven.engine.render:render_pack",
        }
    }
