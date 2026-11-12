from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple
import time
import hashlib
import json

SourceKind = Literal["abraxas_stream", "abraxas_struct", "beatoven_render"]

def _now_ms() -> int:
    return int(time.time() * 1000)

def _stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

@dataclass(frozen=True)
class ResonanceMetrics:
    # All normalized to [0, 1] unless specified.
    complexity: float
    emotional_intensity: float
    groove: float
    energy: float
    density: float
    swing: float
    brightness: float
    tension: float

    def clamp01(self) -> "ResonanceMetrics":
        def c(x: float) -> float:
            return 0.0 if x < 0.0 else 1.0 if x > 1.0 else float(x)
        return ResonanceMetrics(
            complexity=c(self.complexity),
            emotional_intensity=c(self.emotional_intensity),
            groove=c(self.groove),
            energy=c(self.energy),
            density=c(self.density),
            swing=c(self.swing),
            brightness=c(self.brightness),
            tension=c(self.tension),
        )

@dataclass(frozen=True)
class RhythmTokens:
    bpm: float
    meter: Tuple[int, int] = (4, 4)
    # Step grids: each token list is length N steps. A step value is a velocity
    # in [0, 1]; a step fires when its value is above 0 (ADR 0003).
    kick: Optional[List[float]] = None
    snare: Optional[List[float]] = None
    hat: Optional[List[float]] = None
    perc: Optional[List[float]] = None

@dataclass(frozen=True)
class ResonanceFrame:
    id: str
    ts_ms: int
    source: SourceKind

    # Classification / grouping
    genre: Optional[str] = None
    subgenre: Optional[str] = None

    metrics: Optional[ResonanceMetrics] = None
    rhythm: Optional[RhythmTokens] = None

    # Arbitrary extra descriptors (kept deterministic via stable hashing)
    extras: Dict[str, Any] = field(default_factory=dict)

    # Provenance
    abraxas_version: Optional[str] = None
    beatoven_version: Optional[str] = None
    provenance_hash: Optional[str] = None

    def with_provenance_hash(self) -> "ResonanceFrame":
        core = {
            "id": self.id,
            "ts_ms": self.ts_ms,
            "source": self.source,
            "genre": self.genre,
            "subgenre": self.subgenre,
            "metrics": None if self.metrics is None else self.metrics.__dict__,
            "rhythm": None if self.rhythm is None else {
                "bpm": self.rhythm.bpm,
                "meter": self.rhythm.meter,
                "kick": self.rhythm.kick,
                "snare": self.rhythm.snare,
                "hat": self.rhythm.hat,
                "perc": self.rhythm.perc,
            },
            "extras": self.extras,
            "abraxas_version": self.abraxas_version,
            "beatoven_version": self.beatoven_version,
        }
        ph = _stable_hash(core)
        return ResonanceFrame(**{**self.__dict__, "provenance_hash": ph})

    @staticmethod
    def from_source(source: SourceKind, *, id: str, ts_ms: int, **kwargs: Any) -> "ResonanceFrame":
        """Deterministic constructor (ADR 0003): the caller states ``id`` and ``ts_ms``.

        The same arguments always give the same frame and provenance hash.
        """
        return ResonanceFrame(id=id, ts_ms=ts_ms, source=source, **kwargs).with_provenance_hash()

    @staticmethod
    def new(source: SourceKind, **kwargs: Any) -> "ResonanceFrame":
        """NOT deterministic when ``id`` or ``ts_ms`` is omitted: both then come
        from the wall clock. Use ``from_source`` where SEED determinism matters."""
        base = {
            "id": kwargs.pop("id", _stable_hash({"t": _now_ms(), "r": time.perf_counter_ns()})),
            "ts_ms": kwargs.pop("ts_ms", _now_ms()),
            "source": source,
        }
        return ResonanceFrame(**base, **kwargs).with_provenance_hash()

@dataclass(frozen=True)
class FrameDelta:
    """Partial update coming from a live stream; merge into a cached frame."""
    ts_ms: int
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    metrics: Optional[ResonanceMetrics] = None
    rhythm: Optional[RhythmTokens] = None
    extras: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class PresetSelector:
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    # Target ranges for metrics: (min,max) inclusive in [0,1]
    targets: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class PresetBank:
    preset_id: str
    name: str
    selector: PresetSelector

    # Module-specific identifiers
    patch_graph_id: int
    kit_id: Optional[int] = None

    # Macro names are stable contract between BeatOven and dsp.coffee firmware
    macros: List[str] = field(default_factory=list)

    # Safety
    scene_change_quantize: Literal["bar", "beat", "immediate"] = "bar"
    crossfade_ms: int = 150

@dataclass(frozen=True)
class MacroUpdate:
    preset_id: str
    values: Dict[str, float]  # macro -> [0,1] value

@dataclass(frozen=True)
class OpsCommand:
    kind: Literal["LOAD_PRESET", "LOAD_KIT", "COMMIT_PATTERN", "STAGE_NEXT", "PING"]
    payload: Dict[str, Any] = field(default_factory=dict)
