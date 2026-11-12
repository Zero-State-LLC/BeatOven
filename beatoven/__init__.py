"""
BeatOven - Modular Generative Music Engine

A Eurorack-inspired generative music system built on ABX-Core v1.2
and enforced by SEED Protocol for deterministic, reproducible output.

Part of the Applied Alchemy Labs (AAL) ecosystem.
"""

__version__ = "1.1.0"
__author__ = "Applied Alchemy Labs"
__license__ = "Apache-2.0"

from beatoven.core.patchbay import PatchBay
from beatoven.core.input import InputModule
from beatoven.core.translator import SymbolicTranslator
from beatoven.core.rhythm import RhythmEngine
from beatoven.core.harmony import HarmonicEngine
from beatoven.core.timbre import TimbreEngine
from beatoven.core.motion import MotionEngine
from beatoven.core.stems import StemGenerator
from beatoven.core.event_horizon import EventHorizonDetector
from beatoven.core.psyfi import PsyFiIntegration
from beatoven.core.echotome import EchotomeHooks
from beatoven.core.runic_export import RunicVisualExporter

__all__ = [
    "PatchBay",
    "InputModule",
    "SymbolicTranslator",
    "RhythmEngine",
    "HarmonicEngine",
    "TimbreEngine",
    "MotionEngine",
    "StemGenerator",
    "EventHorizonDetector",
    "PsyFiIntegration",
    "EchotomeHooks",
    "RunicVisualExporter",
]
