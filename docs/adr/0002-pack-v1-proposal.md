# 2. BeatOven Pack v1 (proposal)

Status: PROPOSED. Nothing in `beatoven.pack.v0` is changed by this document.

## Context

Pack v0 cannot be played as written (`specs/001-output-module/audit.md` rows 3 and 4): `t` and `dur` have no unit, `cv.clock_hz` is unrelated to `midi.tempo_bpm`, the `CLOCK` and `MOD_CV` lanes share one list of random points, and four allowed lane types are never emitted.

## Proposal

A new schema `beatoven.pack.v1`, emitted alongside v0 until consumers move:

1. Add `midi.time_unit`, required, one of `beats`, `bars`, `seconds`.
2. Either derive `cv.clock_hz` from `tempo_bpm` and a stated pulses-per-quarter value, or drop it.
3. Replace `cv.lanes` with an embedded Output Stream under `output_stream`, so there is one description of what hardware plays.
4. Bump `meta.overlay_version` and the schema `$id`.

## Migration

- `render_pack` keeps its signature and keeps returning v0 by default.
- A `schema_version` argument selects v1.
- The Pack adapter accepts both: for v1 it reads `time_unit` instead of requiring the caller to state it.
- v0 stays readable indefinitely.

## Open

`[NEEDS CLARIFICATION: unit of Pack t and dur]` and `[NEEDS CLARIFICATION: is cv.clock_hz meant to track midi.tempo_bpm]` must be answered first.
