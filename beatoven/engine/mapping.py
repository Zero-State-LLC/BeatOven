import random
from typing import Dict, List

SAFE_PRESETS = {
    "WIND_SHIFT": "AEOLIAN_DRIFT",
    "EMBER": "EMBER_GLOW",
    "MONOLITH": "STONE_PULSE",
    "FROST": "GLASS_STATIC",
}

SCALES = {
    "BRIGHT": [0, 2, 4, 5, 7, 9, 11],
    "DARK": [0, 2, 3, 5, 7, 8, 10],
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def choose_preset(symbolic_modulator: str) -> str:
    return SAFE_PRESETS.get(symbolic_modulator, "SAFE_DEFAULT")


def map_tempo(vector_mix: Dict[str, float], kairos: Dict[str, str]) -> float:
    tempo = 60 + (vector_mix.get("meme_velocity", 0) * 80) + (vector_mix.get("nostalgia", 0) * 20)
    if kairos.get("axis_of_fate") == "REFLECT":
        tempo -= 12
    if kairos.get("framebreaker") == "TIMEBOX":
        tempo += 6
    return round(clamp(tempo, 40, 220), 2)


def map_time_signature(vector_mix: Dict[str, float], kairos: Dict[str, str]) -> Dict[str, int]:
    ritual_density = vector_mix.get("ritual_density", 0)
    if ritual_density > 0.72:
        return {"num": 7, "den": 8}
    if kairos.get("axis_of_fate") == "REFLECT":
        return {"num": 3, "den": 4}
    return {"num": 4, "den": 4}


def map_track_roles(kairos: Dict[str, str]) -> List[str]:
    roles = ["DRUMS", "BASS", "HARMONY", "MELODY"]
    if kairos.get("framebreaker") == "REDUCE_INPUTS":
        return roles[:3]
    if kairos.get("axis_of_fate") == "EXPAND":
        return roles + ["TEXTURE", "FX"]
    return roles


def map_markers(kairos: Dict[str, str]) -> List[Dict[str, str]]:
    binder = kairos.get("continuum_binder", "THREAD")
    axis = kairos.get("axis_of_fate", "CONSOLIDATE")
    return [
        {"t": 0, "label": f"INTRO::{binder}"},
        {"t": 8, "label": f"MOTIF::{axis}"},
        {"t": 16, "label": f"RESOLVE::{binder}"},
    ]


def map_tracks(vector_mix: Dict[str, float], kairos: Dict[str, str], seed: int) -> List[Dict[str, object]]:
    rng = random.Random(seed)
    roles = map_track_roles(kairos)
    tracks = []

    scale_name = "BRIGHT" if vector_mix.get("nostalgia", 0) < 0.5 else "DARK"
    scale = SCALES[scale_name]
    base_pitch = 36 if scale_name == "DARK" else 48

    grid = 0.5 if vector_mix.get("ritual_density", 0) > 0.5 else 1.0
    event_rate = 4 + int(vector_mix.get("meme_velocity", 0) * 4)

    for index, role in enumerate(roles, start=1):
        channel = index
        clip_notes = []
        bars = 4 if kairos.get("framebreaker") == "TIMEBOX" else 8
        for step in range(event_rate):
            time = step * grid
            pitch = base_pitch + scale[step % len(scale)] + (12 if role == "MELODY" else 0)
            velocity = 80 + rng.randint(-10, 10)
            duration = 0.5 if role == "DRUMS" else 0.75
            clip_notes.append(
                {"t": time, "dur": duration, "pitch": pitch, "vel": int(clamp(velocity, 1, 127))}
            )

        cc_lane = {
            "cc": 74,
            "meaning": f"{role}_ENERGY",
            "points": [
                {"t": 0, "v": 64},
                {"t": bars / 2, "v": int(64 + vector_mix.get("meme_velocity", 0) * 48)},
                {"t": bars, "v": 64},
            ],
        }

        tracks.append(
            {
                "name": f"{role.title()} Track",
                "midi_channel": channel,
                "instrument_role": role,
                "program_change": 0,
                "clips": [{"clip_id": f"{role.lower()}_clip", "bars": bars, "notes": clip_notes}],
                "cc_lanes": [cc_lane],
            }
        )

    return tracks


def map_cv(vector_mix: Dict[str, float], seed: int) -> dict:
    rng = random.Random(seed + 77)
    clock_hz = clamp(2 + vector_mix.get("meme_velocity", 0) * 6, 0.1, 30)
    points = [{"t": step * 0.5, "v": round(rng.random(), 3)} for step in range(8)]
    return {
        "clock_hz": clock_hz,
        "lanes": [
            {"lane_type": "CLOCK", "meaning": "GLOBAL_CLOCK", "points": points},
            {"lane_type": "MOD_CV", "meaning": "INTENSITY", "points": points},
        ],
    }
