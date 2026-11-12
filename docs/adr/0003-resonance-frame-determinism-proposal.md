# 3. Deterministic ResonanceFrame identity (proposal)

Status: PROPOSED. `ResonanceFrame` is unchanged by this document.

## Context

`ResonanceFrame.new` fills `id` and `ts_ms` from wall-clock time when the caller omits them (`beatoven/dspcoffee_bridge/schema.py:101-102`). Two runs on the same input then differ, which breaks SEED determinism. `RhythmTokens` documents step values as "probability/velocity" without choosing one.

## Proposal

1. Add `ResonanceFrame.from_source(source, *, id, ts_ms, ...)`, where both are required. Keep `new` as it is and mark it non-deterministic in its docstring.
2. State in `RhythmTokens` that a step value is a velocity in 0 to 1 and that a step fires when it is above 0, or add an explicit `threshold` field.
3. Define `swing` as a fraction of a step by which every second step is delayed, or remove it from the metrics that reach hardware.

## Migration

Additive. No existing call breaks. The adapter keeps requiring `step_threshold` until item 2 is decided.
