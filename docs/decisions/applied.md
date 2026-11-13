# Operator decisions of 2026-11-12: what was applied

The operator accepted every row of [the brief](2026-11-12-operator-decisions.md). This file says what each row changed and what is still waiting.

## Applied in this repository

| Row | Change |
|---|---|
| A2 | Constitution ratified as 1.0.0. |
| A3 | ADRs 0002, 0003 and 0004 marked ACCEPTED; 0002 amended by B1 and B2. None is implemented yet. |
| A5 | Removed `.github/workflows/deploy-azure.yml`, `render.yaml`, `Dockerfile` and `.azure/`. They are in git history. |
| B1 | `from_pack` reads Pack times as bars by default. `time_unit` remains as an override. |
| B2, B3 | The clock comes from `midi.tempo_bpm` at 24 pulses per quarter note by default. `cv.clock_hz` is never used. All adapters default to 24. |
| B4 to B8 | Already the defaults: 0 V at note 12, pitch 0 to +10 V, modulation mapped 0 to +5 V, 5 ms triggers with a 1 ms floor. No code change. |
| B9 | Keepalive timeout is 300 ms (was 500). The driver now sends a sync every 100 ms (was 250) so one late keepalive does not trip it. |
| B10 | A RhythmTokens step fires when its value is above 0. `step_threshold` remains as an override. |
| B11 | Recorded: iOS is not required for v1. |
| B12 | `infer_era_from_heuristics` returns `unknown` when sharpness and saturation are both near zero. The test passes and is no longer marked as an expected failure. |
| C5, C6 | FR-021, FR-022 and SC-005 in the spec restated: static error within ±0.5 mV, a 1 V step within 1 cent inside 200 µs, playout error within 100 µs RMS. |

## A defect found while applying B3

With a 24-per-quarter clock, a stream could end in the middle of a clock pulse, leaving the clock jack high when the stream finished. The adapters now place the clock stop after the last pulse has ended (`_clock_stop_us`). AT-017 covers it.

## The golden vectors changed

`beatoven/output_module/vectors/` was regenerated from the test Pack (seed 7) with the new defaults. **The hardware repository vendors this directory and must take the new copy.**

| | Before | After |
|---|---|---|
| `stream_id` | `453ea6bc…` | `08592ce0…` |
| Trace SHA-256 | `e15b1b3e…` | `ed5f5523…` |
| Host frames | 22 | 90 |
| Duration | 1.82 s | 7.50 s |

Events stay at 77. The stream is four times longer because bars are four beats, and there are more frames because the driver sends a sync every 100 ms.

## Waiting on the operator

| Row | What only the operator can do |
|---|---|
| A1 | Amend Spine 006 and 009 in Notion to say hardware control is allowed by Hardware Lane Grant only, and issue the first grant. The agent writes neither. A grant is a JSON file: `{"schema": "beatoven.hardware_lane_grant.v1", "granted_by": "<name>", "granted_at": "<ISO time>", "scope": ["output_module"], "expires_at": "<ISO time or omit>"}`. No hardware exists to drive yet. |
| A4 | PRs #10 and #11 are closed as duplicates. #12 stays open until it is checked against `main`. |
| D1 | Apply to Raspberry Pi for a product ID. This needs the product's name and a public link, so it waits for D3. |
| D2 | Buy a MIDI Association manufacturer ID before anything ships. |
| D3 | Product name: **BeatOven**, decided by the operator on 2026-11-13 (`2026-11-13-delegated-decisions.md`). |

## Applied in the hardware repository

Rows C1 to C4, C7 and C8 are hardware work and are tracked in Kiln's `docs/rev-a-review-fixes.md` and `hardware/kicad/STATUS.md`.
