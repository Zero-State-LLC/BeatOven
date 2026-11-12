# Next

Updated 2026-11-12, branch `docs/operator-decisions`.

## State

- Board: https://github.com/orgs/Zero-State-LLC/projects/33 (BeatOven + Kiln; Todo, Blocked, In Progress, Done; P0 to P2).

- Software for the Output Module is implemented and tested in simulation: `beatoven/output_module/`, spec in `specs/001-output-module/`.
- Run the checks:
  - `python -m pytest beatoven/output_module` (38 tests; 2 need `python-rtmidi` and a MIDI backend, else they skip)
  - `python scripts/check_spec_trace.py` (traceability; stands in for spec-lint, which is not on this machine)
  - `python -m beatoven.output_module replay-check <stream.json>`
- Hardware is in the Kiln repo. No board exists. Every bench number there is a plan.

## Needs the operator

The operator accepted every recommended answer on 2026-11-12. What was applied is in `docs/decisions/applied.md`. Still the operator's to do:

1. Amend Spine 006 and 009 in Notion and issue the first Hardware Lane Grant (row A1). The agent does neither.
2. Choose the product name (D3), then apply for a Raspberry Pi product ID (D1).
3. Check PR #12 against `main` (A4).

## Next work, in order

1. Implement the accepted ADRs: `beatoven.pack.v1` (0002), ResonanceFrame determinism (0003).
2. Write ADRs for `CLOCK IN` and for calibration commands on the Ops lane.
3. 001-T096: play-on-arrival mode (issue #23).
4. Raise the default look-ahead to 100 ms (issue #24).

## Known issues in the reference device (found while porting to firmware; see Kiln `docs/firmware-architecture.md` §10)

- `sim.py`: timeouts are checked after due events play; `queue_capacity` counts internal entries; fail-closed records the nominal Safe Value, not the quantized one; `ENUMERATING` has no device-side timeout.
- On a one-way link, a host keepalive re-syncs a device that has failed closed. Nothing replays, but the host cannot tell it happened.
- `CLOCK IN` and calibration have no message in the contract yet.

## Measured (software path only)

- Sync round trip over CoreMIDI virtual ports, macOS 26.3.1, Apple M4, 1000 exchanges: p50 916 µs, p99 7375 µs, max 47772 µs. No USB and no hardware in that path. Use a look-ahead of 100 ms or more from a Python host; the default is still 50 ms because the firmware test harness mirrors it.

## Not verified

- Anything on real hardware: latency, jitter, voltage accuracy, power, short-circuit survival.
- The real `spec-lint`.
- Sustained SysEx throughput on any OS.
