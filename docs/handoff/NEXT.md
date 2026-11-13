# Next

Updated 2026-11-13. Operator decisions of 2026-11-12 and 2026-11-13 are applied: Pack v1, `ResonanceFrame.from_source`, 100 ms look-ahead, calibration commands (ADR 0006) and CLOCK IN reports (ADR 0005) in the reference device and driver.

## State

- Board: https://github.com/orgs/Zero-State-LLC/projects/33 (BeatOven + Kiln; Todo, Blocked, In Progress, Done; P0 to P2).

- Software for the Output Module is implemented and tested in simulation: `beatoven/output_module/`, spec in `specs/001-output-module/`.
- Run the checks:
  - `python -m pytest beatoven/output_module` (71 tests; 2 need `python-rtmidi` and a MIDI backend, else they skip)
  - `python scripts/check_spec_trace.py` (traceability; stands in for spec-lint, which is not on this machine)
  - `python -m beatoven.output_module replay-check <stream.json>`
- Hardware is in the Kiln repo. No board exists. Every bench number there is a plan.
- Kiln state on 2026-11-13, branch `hw/kicad-rev-a` at `e7ffa51` or later (nothing is on Kiln `main` yet): the firmware core reproduces the current golden vectors and implements ADRs 0005 and 0006, 3039 checks. The board is fully routed: ERC 0 violations; DRC 0 errors, 0 unconnected, 0 parity issues, 6 `track_dangling` warnings (OBSERVED, re-run at `6d93753`; the board files have not changed since). Each of U1's eight supply pins has its own 100 nF capacitor on the opposite side of the board, 0.15 to 0.34 mm away in plan view, through one via (Kiln issue #7, closed). It is not ready to order: no fabrication outputs exist, about 60 back-side parts moved in the last pass and are unreviewed, and no human has reviewed the board electrically. Nothing has been built. See Kiln `hardware/kicad/STATUS.md`.

## Needs the operator

The product name is **BeatOven** (operator, 2026-11-13). The remaining decisions were delegated to the agent that day and are recorded, with evidence, in `docs/decisions/2026-11-13-delegated-decisions.md`. What only the operator can do:

1. Amend Spine 006 and 009 in Notion and issue the first Hardware Lane Grant. Wording and unsigned grant drafts are in `docs/decisions/hardware-lane-drafts.md`. The agent does neither.
2. Get a trademark lawyer's view before any public launch: BEATOVEN is a live US service mark (registration 7363061) held by an unrelated company, covering music composition and AI music software services.
3. File for a Raspberry Pi USB product ID and buy the MIDI Association's US$240 SysEx ID before anything ships. Both forms need company details.
4. Close PR #12 or keep it. It is not a duplicate; the finding is on the PR and in the decisions file.

## Next work, in order

1. Finish ADRs 0005 and 0006 in Kiln's RP2350 port. The firmware core has them (Kiln `e7ffa51`: 3039 host checks pass, Descriptor byte-identical to the reference, golden vectors unchanged). The port still lacks the CLOCK IN GPIO interrupt and a flash write hook for calibration, and has never been compiled: this Mac has no ARM toolchain.
2. ADR 0007 (play-on-arrival) is PROPOSED and deferred until a board has played an Output Stream on the bench.
3. 001-T096: play-on-arrival mode (issue #23). The mapping is written and tested as a pure function (`beatoven/output_module/arrival.py`, 16 tests); wiring it into the simulated device and Kiln's firmware waits on ADR 0007.

## Known issues in the reference device (found while porting to firmware; see Kiln `docs/firmware-architecture.md` §10)

- `sim.py`: timeouts are checked after due events play; `queue_capacity` counts internal entries; fail-closed records the nominal Safe Value, not the quantized one; `ENUMERATING` has no device-side timeout.
- On a one-way link, a host keepalive re-syncs a device that has failed closed. Nothing replays, but the host cannot tell it happened.
- The grant is checked by the host driver only. The device does not verify one, so other software that speaks the protocol is not bound by it.
- The calibration bounds (±20,000 ppm, ±1,600 sixteenths of an LSB) are a proposal until a board is measured.

## Measured (software path only)

- Sync round trip over CoreMIDI virtual ports, macOS 26.3.1, Apple M4, 1000 exchanges: p50 916 µs, p99 7375 µs, max 47772 µs. No USB and no hardware in that path. The default look-ahead is 100 ms for that reason (issue #24, done 2026-11-12).

## Not verified

- Anything on real hardware: latency, jitter, voltage accuracy, power, short-circuit survival.
- The real `spec-lint`.
- Sustained SysEx throughput on any OS.
