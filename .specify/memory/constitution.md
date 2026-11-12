# BeatOven Constitution

**Version:** 0.1.0 (DRAFT, awaiting operator ratification)
**Drafted:** 2026-11-11
**Authority:** engineering constitution for this repo and the Output Module hardware repo

## Purpose

BeatOven compiles Abraxas Oracle output into music: MIDI, sound-design intent, arrangement, and an Output Stream a device can play. This constitution constrains every feature specification and implementation.

## Non-negotiable principles

1. **SEED determinism.** Identical inputs, seed and versions MUST produce byte-identical outputs. Every output carries the hashes of its inputs. Wall-clock time and unseeded randomness MUST NOT influence an output.
2. **Determinism reaches the device.** An Output Stream is content-addressed. A device that plays it MUST be able to report a hash of what it played.
3. **PsyFi owns visualization.** BeatOven MUST NOT render, claim or own visual output. It may export a packet for PsyFi.
4. **Fail closed at trust boundaries.** A malformed packet, unknown version, missing grant, late event or lost clock MUST become an explicit error or safe state. It is never an implicit pass and never a best-effort guess.
5. **Unknown remains unknown.** A missing unit, range or meaning MUST NOT be invented. The caller states it, or the result is marked `NOT_COMPUTABLE`.
6. **Every value has a unit.** A contract that crosses to hardware carries time, voltage and width in named units. Unitless numbers stop at an adapter.
7. **Hardware lane authority.** `hardware_control_allowed` is false by default, as canon states. A device may be driven only under a named, scoped, operator-issued grant. Simulation needs no grant. *Pending: `[NEEDS CLARIFICATION: operator decision on hardware lane authority]`. Until it is resolved, this principle is the binding rule.*
8. **Public shapes change by proposal.** Existing public names and schemas change only through a written proposal with a migration and a version bump.
9. **Provenance is mandatory.** A claim of "done", "passing" or "measured" needs the output that shows it. A plan is labelled a plan.

## Required specification chain

Every capability MUST trace:

`Journey -> Workflow -> State Transition -> Contract -> Acceptance Test -> Implementation Task`.

## Evidence labels

- **OBSERVED**: read in a cited source, or measured.
- **INFERRED**: derived, with the basis stated.
- **SPECULATIVE**: hypothesis only.
- **NOT_COMPUTABLE**: the required fact is absent.

## Change control

A feature spec may strengthen this constitution but may not weaken it. A weakening needs a version change, an impact analysis and operator approval.
