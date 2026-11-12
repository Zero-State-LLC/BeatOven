"""Device connection lifecycle.

One transitions table, used by the host driver, the simulated Output Module
and (exported as JSON) the firmware. Anything not in the table is illegal.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Tuple


class State(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    ENUMERATING = "ENUMERATING"
    SYNCED = "SYNCED"
    STREAMING = "STREAMING"
    TIMING_LOST = "TIMING_LOST"
    SAFE_IDLE = "SAFE_IDLE"


class Event(str, Enum):
    ATTACH = "attach"
    SYNC_OK = "sync_ok"
    REJECT = "reject"
    STREAM_BEGIN = "stream_begin"
    STREAM_END = "stream_end"
    TIMING_LOSS = "timing_loss"
    SAFE_REACHED = "safe_reached"
    RESYNC = "resync"
    DETACH = "detach"


class LossReason(str, Enum):
    LATE_EVENT = "LATE_EVENT"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    INTEGRITY = "INTEGRITY"
    KEEPALIVE_TIMEOUT = "KEEPALIVE_TIMEOUT"
    SYNC_TIMEOUT = "SYNC_TIMEOUT"
    QUEUE_OVERFLOW = "QUEUE_OVERFLOW"
    HOST_ABORT = "HOST_ABORT"


INITIAL = State.DISCONNECTED
FINAL = (State.DISCONNECTED,)

# (from, event) -> (guard, to, effect)
TRANSITIONS: Dict[Tuple[State, Event], Tuple[str, State, str]] = {
    (State.DISCONNECTED, Event.ATTACH): (
        "transport link is up", State.ENUMERATING, "drive all outputs safe; exchange the Descriptor"),
    (State.ENUMERATING, Event.SYNC_OK): (
        "Descriptor accepted, contract version matches, hardware lane granted",
        State.SYNCED, "record the clock offset"),
    (State.ENUMERATING, Event.REJECT): (
        "Descriptor invalid, version mismatch, or hardware lane denied",
        State.SAFE_IDLE, "outputs stay safe; report the reason"),
    (State.SYNCED, Event.STREAM_BEGIN): (
        "stream fits the Descriptor and starts at least min lead in the future",
        State.STREAMING, "arm the scheduler"),
    (State.SYNCED, Event.TIMING_LOSS): (
        "no sync within the sync timeout", State.TIMING_LOST, "apply fail-closed outputs"),
    (State.STREAMING, Event.STREAM_END): (
        "every event has played", State.SYNCED, "gates low, clock stopped, CV held; report the played hash"),
    (State.STREAMING, Event.TIMING_LOSS): (
        "late event, sequence gap, integrity failure, keepalive timeout, overflow or host abort",
        State.TIMING_LOST, "drop the queue; apply fail-closed outputs"),
    (State.TIMING_LOST, Event.SAFE_REACHED): (
        "every output is at its safe value", State.SAFE_IDLE, "report status"),
    (State.SAFE_IDLE, Event.RESYNC): (
        "a fresh sync exchange succeeded", State.SYNCED, "record the clock offset"),
}
# Detach is legal from every connected state.
for _s in State:
    if _s is not State.DISCONNECTED:
        TRANSITIONS[(_s, Event.DETACH)] = (
            "transport link is down", State.DISCONNECTED, "drive all outputs safe")


class IllegalTransition(RuntimeError):
    pass


class Lifecycle:
    def __init__(self) -> None:
        self.state = INITIAL
        self.history: List[Tuple[State, Event, State]] = []

    def can(self, event: Event) -> bool:
        return (self.state, event) in TRANSITIONS

    def fire(self, event: Event) -> State:
        key = (self.state, event)
        if key not in TRANSITIONS:
            raise IllegalTransition(f"{event.value} is illegal in {self.state.value}")
        new = TRANSITIONS[key][1]
        self.history.append((self.state, event, new))
        self.state = new
        return new


def illegal_transitions() -> List[Tuple[State, Event]]:
    return [(s, e) for s in State for e in Event if (s, e) not in TRANSITIONS]


def as_table() -> List[Dict[str, str]]:
    """The table in the spec's column order: from | event | guard | to | effect."""
    return [
        {"from": s.value, "event": e.value, "guard": g, "to": t.value, "effect": fx}
        for (s, e), (g, t, fx) in sorted(TRANSITIONS.items(), key=lambda kv: (list(State).index(kv[0][0]), kv[0][1].value))
    ]
