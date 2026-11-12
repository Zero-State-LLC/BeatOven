# 2. BeatOven Pack v1 (proposal)

Status: ACCEPTED by the operator on 2026-11-12, with two amendments: the time unit is bars (decision B1), and `cv.clock_hz` is dropped in favour of a clock derived from `tempo_bpm` at 24 pulses per quarter note by default (decisions B2, B3). Implemented on 2026-11-12: `render_pack(..., schema_version="v1")` and `beatoven/schemas/beatoven.pack.v1.schema.json`. `beatoven.pack.v0` is unchanged and remains the default.

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

Both questions are answered (see Status). Until v1 exists, the Pack adapter applies the same two rules to v0.
