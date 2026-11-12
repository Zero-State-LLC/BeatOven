"""
BeatOven Symbolic Translator

Converts input symbolic vectors into ABX-Runes semantic fields:
resonance, density, drift, tension, contrast.
"""

import hashlib
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ABXRunesFields:
    """
    ABX-Runes semantic fields output.

    These five fields control the generative characteristics:
    - resonance: Harmonic richness and sustain (0.0-1.0)
    - density: Event density and complexity (0.0-1.0)
    - drift: Temporal variation and evolution (0.0-1.0)
    - tension: Harmonic/rhythmic tension level (0.0-1.0)
    - contrast: Dynamic range and variation (0.0-1.0)
    """
    resonance: float
    density: float
    drift: float
    tension: float
    contrast: float

    # Extended field vectors for fine-grained control
    resonance_spectrum: np.ndarray = field(default_factory=lambda: np.zeros(16, dtype=np.float32))
    density_layers: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))
    drift_curves: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))
    tension_harmonics: np.ndarray = field(default_factory=lambda: np.zeros(12, dtype=np.float32))
    contrast_dynamics: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))

    provenance_hash: str = ""

    def __post_init__(self):
        # Clamp all primary values
        self.resonance = max(0.0, min(1.0, self.resonance))
        self.density = max(0.0, min(1.0, self.density))
        self.drift = max(0.0, min(1.0, self.drift))
        self.tension = max(0.0, min(1.0, self.tension))
        self.contrast = max(0.0, min(1.0, self.contrast))

    def to_vector(self) -> np.ndarray:
        """Flatten all fields to single vector."""
        primary = np.array([
            self.resonance, self.density, self.drift,
            self.tension, self.contrast
        ], dtype=np.float32)
        return np.concatenate([
            primary,
            self.resonance_spectrum,
            self.density_layers,
            self.drift_curves,
            self.tension_harmonics,
            self.contrast_dynamics
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "resonance": self.resonance,
            "density": self.density,
            "drift": self.drift,
            "tension": self.tension,
            "contrast": self.contrast,
            "resonance_spectrum": self.resonance_spectrum.tolist(),
            "density_layers": self.density_layers.tolist(),
            "drift_curves": self.drift_curves.tolist(),
            "tension_harmonics": self.tension_harmonics.tolist(),
            "contrast_dynamics": self.contrast_dynamics.tolist(),
            "provenance_hash": self.provenance_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ABXRunesFields":
        """Deserialize from dictionary."""
        return cls(
            resonance=data["resonance"],
            density=data["density"],
            drift=data["drift"],
            tension=data["tension"],
            contrast=data["contrast"],
            resonance_spectrum=np.array(data.get("resonance_spectrum", np.zeros(16)), dtype=np.float32),
            density_layers=np.array(data.get("density_layers", np.zeros(8)), dtype=np.float32),
            drift_curves=np.array(data.get("drift_curves", np.zeros(8)), dtype=np.float32),
            tension_harmonics=np.array(data.get("tension_harmonics", np.zeros(12)), dtype=np.float32),
            contrast_dynamics=np.array(data.get("contrast_dynamics", np.zeros(8)), dtype=np.float32),
            provenance_hash=data.get("provenance_hash", "")
        )


class SymbolicTranslator:
    """
    Translates symbolic vectors from InputModule into ABX-Runes semantic fields.

    Uses deterministic neural-inspired projections to map high-dimensional
    input embeddings to the five core ABX-Runes fields plus their extended vectors.
    """

    def __init__(self, compression_factor: float = 0.8):
        """
        Initialize translator.

        Args:
            compression_factor: ABX-Core entropy compression (0.0-1.0)
        """
        self.compression_factor = max(0.0, min(1.0, compression_factor))
        self._init_projection_matrices()

    def _init_projection_matrices(self):
        """Initialize deterministic projection matrices."""
        # Use fixed seed for deterministic projections
        rng = np.random.default_rng(0xABC012E)

        # Input dimensions: intent(128) + mood(32) + rune(64) + style(18) = 242
        input_dim = 242

        # Primary field projections
        self._resonance_proj = rng.standard_normal((input_dim, 1)).astype(np.float32) / np.sqrt(input_dim)
        self._density_proj = rng.standard_normal((input_dim, 1)).astype(np.float32) / np.sqrt(input_dim)
        self._drift_proj = rng.standard_normal((input_dim, 1)).astype(np.float32) / np.sqrt(input_dim)
        self._tension_proj = rng.standard_normal((input_dim, 1)).astype(np.float32) / np.sqrt(input_dim)
        self._contrast_proj = rng.standard_normal((input_dim, 1)).astype(np.float32) / np.sqrt(input_dim)

        # Extended field projections
        self._resonance_spectrum_proj = rng.standard_normal((input_dim, 16)).astype(np.float32) / np.sqrt(input_dim)
        self._density_layers_proj = rng.standard_normal((input_dim, 8)).astype(np.float32) / np.sqrt(input_dim)
        self._drift_curves_proj = rng.standard_normal((input_dim, 8)).astype(np.float32) / np.sqrt(input_dim)
        self._tension_harmonics_proj = rng.standard_normal((input_dim, 12)).astype(np.float32) / np.sqrt(input_dim)
        self._contrast_dynamics_proj = rng.standard_normal((input_dim, 8)).astype(np.float32) / np.sqrt(input_dim)

    def translate(
        self,
        intent_embedding: np.ndarray,
        mood_vector: np.ndarray,
        rune_vector: np.ndarray,
        style_vector: np.ndarray,
        input_provenance: str = ""
    ) -> ABXRunesFields:
        """
        Translate symbolic vectors to ABX-Runes fields.

        Args:
            intent_embedding: 128-dim intent vector
            mood_vector: 32-dim mood vector
            rune_vector: 64-dim rune vector
            style_vector: 18-dim style vector
            input_provenance: Provenance hash from input module

        Returns:
            ABXRunesFields containing all semantic fields
        """
        # Concatenate all inputs
        combined = np.concatenate([
            intent_embedding.flatten(),
            mood_vector.flatten(),
            rune_vector.flatten(),
            style_vector.flatten()
        ]).astype(np.float32)

        # Pad or truncate to expected dimension
        expected_dim = 242
        if len(combined) < expected_dim:
            combined = np.pad(combined, (0, expected_dim - len(combined)))
        elif len(combined) > expected_dim:
            combined = combined[:expected_dim]

        # Apply ABX-Core entropy compression
        combined = self._apply_compression(combined)

        # Project to primary fields (sigmoid activation for 0-1 range)
        resonance = float(self._sigmoid(combined @ self._resonance_proj).item())
        density = float(self._sigmoid(combined @ self._density_proj).item())
        drift = float(self._sigmoid(combined @ self._drift_proj).item())
        tension = float(self._sigmoid(combined @ self._tension_proj).item())
        contrast = float(self._sigmoid(combined @ self._contrast_proj).item())

        # Project to extended fields (tanh activation for -1 to 1)
        resonance_spectrum = np.tanh(combined @ self._resonance_spectrum_proj).astype(np.float32)
        density_layers = np.tanh(combined @ self._density_layers_proj).astype(np.float32)
        drift_curves = np.tanh(combined @ self._drift_curves_proj).astype(np.float32)
        tension_harmonics = np.tanh(combined @ self._tension_harmonics_proj).astype(np.float32)
        contrast_dynamics = np.tanh(combined @ self._contrast_dynamics_proj).astype(np.float32)

        # Compute provenance hash
        provenance_hash = self._compute_provenance(
            resonance, density, drift, tension, contrast, input_provenance
        )

        return ABXRunesFields(
            resonance=resonance,
            density=density,
            drift=drift,
            tension=tension,
            contrast=contrast,
            resonance_spectrum=resonance_spectrum,
            density_layers=density_layers,
            drift_curves=drift_curves,
            tension_harmonics=tension_harmonics,
            contrast_dynamics=contrast_dynamics,
            provenance_hash=provenance_hash
        )

    def _apply_compression(self, vector: np.ndarray) -> np.ndarray:
        """Apply ABX-Core entropy compression."""
        # Soft compression toward mean
        mean = np.mean(vector)
        compressed = mean + self.compression_factor * (vector - mean)
        return compressed

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return np.where(
            x >= 0,
            1 / (1 + np.exp(-x)),
            np.exp(x) / (1 + np.exp(x))
        )

    def _compute_provenance(
        self,
        resonance: float,
        density: float,
        drift: float,
        tension: float,
        contrast: float,
        input_provenance: str
    ) -> str:
        """Compute provenance hash for translation output."""
        data = f"{resonance:.6f}:{density:.6f}:{drift:.6f}:{tension:.6f}:{contrast:.6f}:{input_provenance}"
        return hashlib.sha256(data.encode()).hexdigest()


__all__ = ["SymbolicTranslator", "ABXRunesFields"]
