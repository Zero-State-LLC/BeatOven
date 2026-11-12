from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Tuple

from beatoven.engine import determinism
from beatoven.engine.hashing import hash_file, hash_pack, sha256_json
from beatoven.engine.mapping import (
    choose_preset,
    map_cv,
    map_markers,
    map_tempo,
    map_time_signature,
    map_tracks,
)

OVERLAY_VERSION = "0.1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "beatoven.pack.v0.schema.json"

# beatoven.pack.v1 (ADR 0002, accepted 2026-11-12). v0 stays the default.
PACK_V1_SCHEMA = "beatoven.pack.v1"
PACK_V1_OVERLAY_VERSION = "1.0.0"
PACK_V1_TIME_UNIT = "bars"
PACK_V1_CLOCK_PPQN = 24
SCHEMA_V1_PATH = SCHEMA_PATH.with_name("beatoven.pack.v1.schema.json")


def _validate_oracle(oracle_v2: dict) -> None:
    if "vector_mix" not in oracle_v2 or "kairos" not in oracle_v2:
        raise ValueError("oracle_v2 must include vector_mix and kairos")


def _deterministic_timestamp(seed: int) -> str:
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    return (base + timedelta(seconds=seed)).isoformat()


def _build_session_recipe(daw: str, tracks: list, kairos: dict) -> dict:
    daw_upper = daw.upper()
    daw_targets = [daw_upper] if daw_upper in {"ABLETON", "LOGIC", "FL_STUDIO", "REAPER", "BITWIG"} else ["GENERIC"]
    if "GENERIC" not in daw_targets:
        daw_targets.append("GENERIC")

    routing = []
    for track in tracks:
        routing.append(
            {
                "track": track["name"],
                "target": f"MIDI CH {track['midi_channel']}",
                "notes": "Import clip + map CC74 to macro for energy contour.",
            }
        )

    export_steps = [
        f"Set tempo + time signature in {daw_targets[0]}.",
        "Create MIDI tracks and set channels as listed.",
        "Import clips, align to markers, and map CC lanes.",
        f"Honor silent sovereign: {kairos.get('silent_sovereign', 'FOCUS_ONE_MOVE')}",
    ]

    return {"daw_targets": daw_targets, "routing": routing, "export_steps": export_steps}


def _session_recipe_markdown(session_recipe: dict) -> str:
    lines = ["# BeatOven Session Recipe", "", "## DAW Targets"]
    lines.extend([f"- {daw}" for daw in session_recipe["daw_targets"]])
    lines.append("")
    lines.append("## Routing")
    for route in session_recipe["routing"]:
        lines.append(f"- {route['track']} -> {route['target']} ({route['notes']})")
    lines.append("")
    lines.append("## Export Steps")
    for step in session_recipe["export_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines)


def _input_hashes(oracle_v2: dict, overlays: dict, schema_path: Path = SCHEMA_PATH,
                  code_version: str = OVERLAY_VERSION) -> dict:
    schema_hash = hash_file(schema_path) if schema_path.exists() else "missing"
    return {
        "oracle_signal_layer_v2": sha256_json(oracle_v2),
        "overlays": sha256_json(overlays),
        "schema": schema_hash,
        "code_version": code_version,
    }


def _overlay_status(overlays: dict) -> dict:
    status = {}
    if overlays.get("abx_gt"):
        status["abx_gt"] = "present"
    else:
        status["abx_gt"] = "not_computable"
    return status


def render_pack(
    oracle_v2: dict, overlays: dict, seed: int, daw: str, test_mode: bool = False,
    *, schema_version: str = "v0",
) -> dict:
    """Render a BeatOven Pack.

    ``schema_version="v0"`` (the default) returns ``beatoven.pack.v0`` exactly
    as before. ``"v1"`` returns ``beatoven.pack.v1``: times are stated to be in
    bars, the clock is stated as pulses per quarter note, ``cv`` is gone, and
    the compiled Output Stream is embedded under ``output_stream``.
    """
    if schema_version not in ("v0", "v1"):
        raise ValueError(f"unknown schema_version: {schema_version!r}")
    v1 = schema_version == "v1"
    _validate_oracle(oracle_v2)
    vector_mix = oracle_v2["vector_mix"]
    kairos = oracle_v2["kairos"]

    tempo_bpm = map_tempo(vector_mix, kairos)
    time_signature = map_time_signature(vector_mix, kairos)
    tracks = map_tracks(vector_mix, kairos, seed)
    markers = map_markers(kairos)

    pack = {
        "meta": {
            "overlay_id": "beatoven",
            "overlay_version": OVERLAY_VERSION,
            "generated_at_utc": _deterministic_timestamp(seed),
        },
        "seed": seed,
        "inputs": {
            "vector_mix": {
                "ritual_density": vector_mix.get("ritual_density"),
                "meme_velocity": vector_mix.get("meme_velocity"),
                "nostalgia": vector_mix.get("nostalgia"),
                "symbolic_modulator": choose_preset(vector_mix.get("symbolic_modulator", "SAFE_DEFAULT")),
            },
            "kairos": kairos,
            "overlays": _overlay_status(overlays),
        },
        "midi": {
            "tempo_bpm": tempo_bpm,
            "time_signature": time_signature,
            "tracks": tracks,
            "markers": markers,
        },
        "session_recipe": _build_session_recipe(daw, tracks, kairos),
        "provenance": {
            "input_hashes": _input_hashes(oracle_v2, overlays),
            "output_hashes": {},
            "determinism": {"mode": "SEED", "twelve_run_invariance": True},
            "overlay_status": _overlay_status(overlays),
        },
    }

    if v1:
        pack["meta"]["schema"] = PACK_V1_SCHEMA
        pack["meta"]["overlay_version"] = PACK_V1_OVERLAY_VERSION
        pack["midi"]["time_unit"] = PACK_V1_TIME_UNIT
        pack["midi"]["clock_ppqn"] = PACK_V1_CLOCK_PPQN
        pack["provenance"]["input_hashes"] = _input_hashes(
            oracle_v2, overlays, SCHEMA_V1_PATH, PACK_V1_OVERLAY_VERSION)
        from beatoven.output_module.adapters import from_pack  # imported here: output_module imports nothing from engine
        pack["output_stream"] = from_pack(pack).to_dict()
    elif vector_mix.get("meme_velocity", 0) > 0.55:
        pack["cv"] = map_cv(vector_mix, seed)

    if test_mode:
        _, invariance = determinism.run_n_times(
            lambda: render_pack(oracle_v2, overlays, seed, daw, test_mode=False, schema_version=schema_version)
        )
        if not invariance:
            raise RuntimeError("Determinism drift detected")
        pack["provenance"]["determinism"]["twelve_run_invariance"] = invariance

    output_hashes = {
        "pack": hash_pack(pack),
        "session_recipe_md": sha256_json(_session_recipe_markdown(pack["session_recipe"])),
    }
    if pack.get("cv"):
        output_hashes["cv"] = sha256_json(pack["cv"])
    if pack.get("output_stream"):
        output_hashes["output_stream"] = pack["output_stream"]["stream_id"]

    pack["provenance"]["output_hashes"] = output_hashes
    return pack


def render_report_bundle(pack: dict) -> Dict[str, dict]:
    session_recipe_md = _session_recipe_markdown(pack["session_recipe"])
    determinism_report = {
        "overlay_version": pack["meta"]["overlay_version"],
        "twelve_run_invariance": pack["provenance"]["determinism"]["twelve_run_invariance"],
        "mode": pack["provenance"]["determinism"]["mode"],
        "notes": "stable" if pack["provenance"]["determinism"]["twelve_run_invariance"] else "drift",
    }
    provenance_manifest = {
        "input_hashes": pack["provenance"]["input_hashes"],
        "output_hashes": pack["provenance"]["output_hashes"],
        "overlay_version": pack["meta"]["overlay_version"],
        "seed": pack["seed"],
        "generated_at_utc": pack["meta"]["generated_at_utc"],
    }
    return {
        "session_recipe_md": session_recipe_md,
        "determinism_report": determinism_report,
        "provenance_manifest": provenance_manifest,
    }
