# Next

Updated 2026-11-11, branch `feat/output-module-contract`.

## State

- Board: https://github.com/orgs/Zero-State-LLC/projects/33 (BeatOven + Kiln; Todo, Blocked, In Progress, Done; P0 to P2).

- Software for the Output Module is implemented and tested in simulation: `beatoven/output_module/`, spec in `specs/001-output-module/`.
- Run the checks:
  - `python -m pytest beatoven/output_module` (36 tests; 2 need `python-rtmidi` and a MIDI backend, else they skip)
  - `python scripts/check_spec_trace.py` (traceability; stands in for spec-lint, which is not on this machine)
  - `python -m beatoven.output_module replay-check <stream.json>`
- Hardware is in the Kiln repo. No board exists. Every bench number there is a plan.

## Needs the operator

Every open decision has a recommended answer in `docs/decisions/2026-11-12-operator-decisions.md`. Reply with the row numbers you accept.

A second research pass is in `docs/decisions/research/open-questions.md`. It closed 12 questions, lists the answers that were rejected, and names what is still open. It also corrected Kiln's power budget: 51.7 mA on +12 V and 20.5 mA on −12 V, calculated.

0. Install KiCad 10 (`brew install --cask kicad` asks for your password). Schematic, ERC, DRC and Gerbers are blocked on it.

1. Hardware lane authority: amend Spine 006/009 or issue a scoped grant. Until then nothing may drive a device.
2. The other clarifications in `specs/001-output-module/spec.md`, "Open clarifications".
3. Ratify `.specify/memory/constitution.md` (DRAFT 0.1.0).

## Next work, in order

3. 001-T095: decide `beatoven/media_intel/tests/test_temporal.py::test_infer_era_unknown` (test and code disagree; the only failing test in the repo once `opencv-python-headless` is installed).
4. 001-T096: play-on-arrival mode.
5. Rule on the PROPOSED ADRs in `docs/adr/` (0002 to 0004).

## Known issues in the reference device (found while porting to firmware; see Kiln `docs/firmware-architecture.md` §10)

- `sim.py`: timeouts are checked after due events play; `queue_capacity` counts internal entries; fail-closed records the nominal Safe Value, not the quantized one; `ENUMERATING` has no device-side timeout.
- The "≤ 2 ms p99 latency" target conflicts with scheduled playout (events are sent 20–70 ms early). It should probably be restated as playout error. Operator call.
- On a one-way link, a host keepalive re-syncs a device that has failed closed. Nothing replays, but the host cannot tell it happened.
- `CLOCK IN` and calibration have no message in the contract yet.

## Measured (software path only)

- Sync round trip over CoreMIDI virtual ports, macOS 26.3.1, Apple M4, 1000 exchanges: p50 916 µs, p99 7375 µs, max 47772 µs. No USB and no hardware in that path. Use a look-ahead of 100 ms or more from a Python host; the default is still 50 ms because the firmware test harness mirrors it.

## Not verified

- Anything on real hardware: latency, jitter, voltage accuracy, power, short-circuit survival.
- The real `spec-lint`.
- Sustained SysEx throughput on any OS.
