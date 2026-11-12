"""Hardware lane authority.

Canon (PATCH-GLOBAL-SPINE-006 and -009) sets ``hardware_control_allowed:
false``. This module keeps that default. Only an operator-issued grant file
opens the hardware lane, and only for the scope it names. Simulation needs no
grant because it drives no hardware.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

GRANT_SCHEMA = "beatoven.hardware_lane_grant.v1"
SCOPE = "output_module"


class HardwareLaneDenied(PermissionError):
    pass


@dataclass(frozen=True)
class HardwareLaneGrant:
    granted_by: str
    granted_at: str
    scope: tuple
    expires_at: Optional[str] = None

    @staticmethod
    def load(path: Path) -> "HardwareLaneGrant":
        try:
            d = json.loads(Path(path).read_text())
        except (OSError, ValueError) as exc:
            raise HardwareLaneDenied(f"grant file unreadable: {exc}") from exc
        if d.get("schema") != GRANT_SCHEMA or not d.get("granted_by") or not d.get("granted_at"):
            raise HardwareLaneDenied("grant file is not a valid hardware lane grant")
        return HardwareLaneGrant(d["granted_by"], d["granted_at"], tuple(d.get("scope", ())), d.get("expires_at"))

    def check(self, now: Optional[datetime] = None) -> None:
        if SCOPE not in self.scope:
            raise HardwareLaneDenied(f"grant does not cover scope {SCOPE!r}")
        if self.expires_at is not None:
            now = now or datetime.now(timezone.utc)
            if now >= datetime.fromisoformat(self.expires_at):
                raise HardwareLaneDenied("grant has expired")


def require_hardware_lane(grant: Optional[HardwareLaneGrant], *, simulated: bool) -> None:
    """Raise unless this transport may be driven. Default is deny."""
    if simulated:
        return
    if grant is None:
        raise HardwareLaneDenied("hardware_control_allowed is false: no operator grant supplied")
    grant.check()
