"""The Output Module (PROPOSED name): BeatOven's canonical hardware contract,
adapters from the existing contracts, the host driver and a simulated device.

Importing this package drives no hardware. Real transports need an operator
grant; see ``authority.py``.
"""

from .adapters import (
    from_audio_control_frames,
    from_cv_gate_map,
    from_midi_event_stream,
    from_pack,
    from_resonance_frame,
)
from .authority import HardwareLaneDenied, HardwareLaneGrant
from .contract import (
    CONTRACT_VERSION,
    Channel,
    ChannelKind,
    ContractError,
    Descriptor,
    Op,
    OutputEvent,
    OutputStream,
    reference_descriptor,
)
from .driver import LoopbackTransport, OneWayLoopbackTransport, OutputModuleDriver, PlayReport, VirtualClock
from .lifecycle import Event, IllegalTransition, Lifecycle, LossReason, State
from .sim import SimulatedOutputModule

__all__ = [
    "CONTRACT_VERSION", "Channel", "ChannelKind", "ContractError", "Descriptor", "Op",
    "OutputEvent", "OutputStream", "reference_descriptor",
    "from_pack", "from_resonance_frame", "from_audio_control_frames", "from_cv_gate_map",
    "from_midi_event_stream",
    "HardwareLaneDenied", "HardwareLaneGrant",
    "OutputModuleDriver", "LoopbackTransport", "OneWayLoopbackTransport", "PlayReport", "VirtualClock",
    "SimulatedOutputModule", "Lifecycle", "State", "Event", "LossReason", "IllegalTransition",
]
