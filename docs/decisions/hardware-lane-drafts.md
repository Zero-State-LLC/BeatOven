# Hardware Lane: drafts for the operator to sign

Status: DRAFT text. The operator stated on 2026-11-13 that a grant has been signed and the Spine pages amended; the signed grant is not in this repository and the amendment could not be confirmed by a read that day (`FACTS.md`). The text below is the draft as offered, not a record of what was signed. The agent does not issue a Hardware Lane Grant and does not edit Notion; both are the operator's acts (`FACTS.md`, 2026-11-12). These drafts exist so that issuing them is a copy and a signature, not a writing task. Tracked in issue #18.

## 1. Proposed amendment to Spine 006 and 009

Both pages state `hardware_control_allowed: false`. Proposed replacement wording, the same in each:

> `hardware_control_allowed: false`, except under a Hardware Lane Grant.
>
> A Hardware Lane Grant is the operator's written permission to drive a physical device. It names its scope, who granted it and when, and may state an expiry. Without a grant that names the scope, software and agents MUST NOT drive hardware. Simulation drives no hardware and needs no grant.
>
> Scopes defined so far: `output_module` (connect to and play an Output Stream on an Output Module) and `output_module.calibrate` (change an Output Module's stored calibration; a grant naming it MUST state an expiry). Neither scope implies the other.
>
> The grant binds Zero State's software and agents. A device does not verify it.

What this wording matches in the repository (OBSERVED): `beatoven/output_module/authority.py`, spec FR-017 and FR-029, ADR 0006.

## 2. Draft grant: play

Not valid as written: `granted_by` and `granted_at` are empty, and `HardwareLaneGrant.load` rejects a grant without them. Save outside the repository once filled in; a grant file is never committed.

```json
{
  "schema": "beatoven.hardware_lane_grant.v1",
  "granted_by": "",
  "granted_at": "",
  "scope": ["output_module"],
  "expires_at": null
}
```

- `granted_at` and `expires_at` are ISO 8601 with a zone, for example `2026-12-01T00:00:00+00:00`.
- `expires_at` may stay `null` for a play grant. A dated expiry is still the safer choice while there is one prototype on one bench.

## 3. Draft grant: bench calibration session

Also not valid as written. The calibrate scope must have an expiry, and a session needs the play scope too, because calibration plays a stream of known voltages.

```json
{
  "schema": "beatoven.hardware_lane_grant.v1",
  "granted_by": "",
  "granted_at": "",
  "scope": ["output_module", "output_module.calibrate"],
  "expires_at": ""
}
```

## 4. What stays closed whatever is signed

- Play-on-arrival (ADR 0007) is PROPOSED and deferred. No grant opens it, because no device implements it.
- No command outputs a raw DAC code (`CAL_RAW` was dropped, ADR 0006).
- No hardware exists yet. Until a board is built, a grant has nothing to open.
