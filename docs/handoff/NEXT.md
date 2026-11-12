# Next

Updated 2026-11-11, branch `feat/output-module-contract`.

## State

- Software for the Output Module is implemented and tested in simulation: `beatoven/output_module/`, spec in `specs/001-output-module/`.
- Run the checks:
  - `python -m pytest beatoven/output_module` (32 tests)
  - `python scripts/check_spec_trace.py` (traceability; stands in for spec-lint, which is not on this machine)
  - `python -m beatoven.output_module replay-check <stream.json>`
- Hardware is in the Kiln repo. No board exists. Every bench number there is a plan.

## Needs the operator

0. Install KiCad 10 (`brew install --cask kicad` asks for your password). Schematic, ERC, DRC and Gerbers are blocked on it.

1. Hardware lane authority: amend Spine 006/009 or issue a scoped grant. Until then nothing may drive a device.
2. The other clarifications in `specs/001-output-module/spec.md`, "Open clarifications".
3. Ratify `.specify/memory/constitution.md` (DRAFT 0.1.0).

## Next work, in order

1. 001-T045: write the Pack v1, ResonanceFrame and MIDIEventStream.v1 proposals as ADRs.
2. 001-T056: real MIDI port transport, behind the grant. Needs a device or a loopback port.
3. 001-T092: fix the tests that fail on `main` (`beatoven/tests/test_api.py`, `test_doctrine.py`; `media_intel` needs `cv2`).
4. 001-T093: TRS one-way mode and play-on-arrival mode.

## Known issues in the reference device (found while porting to firmware; see Kiln `docs/firmware-architecture.md` §10)

- `driver.py`: the clock offset is computed once at connect. Sync replies during play are dropped, so drift is not corrected within a stream.
- `sim.py`: timeouts are checked after due events play; `queue_capacity` counts internal entries; fail-closed records the nominal Safe Value, not the quantized one; `ENUMERATING` has no device-side timeout.
- `wire.py`: the group-MSB byte and the seq byte are not checked for bit 7.
- `vectors/manifest.json` has no per-frame send times; the firmware harness re-derives them.
- The "≤ 2 ms p99 latency" target conflicts with scheduled playout (events are sent 20–70 ms early). It should probably be restated as playout error. Operator call.
- TRS fallback: a 16-event frame takes 87 ms at MIDI speed, longer than the 50 ms look-ahead. The fallback needs smaller frames and a longer look-ahead.
- `CLOCK IN` and calibration have no message in the contract yet.

## Not verified

- Anything on real hardware: latency, jitter, voltage accuracy, power, short-circuit survival.
- The real `spec-lint`.
- Sustained SysEx throughput on any OS.
