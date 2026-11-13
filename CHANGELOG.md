# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Schema identifiers such as `beatoven.pack.v0` and `beatoven.output_stream.v1` are versioned on their own and do not follow the package version.

## [Unreleased]

### Added

- Calibration commands on the Ops Lane (ADR 0006, accepted): `CAL_READ`, `CAL_WRITE`, `CAL_REVERT`, with `OutputModuleDriver.cal_read`, `cal_write` and `cal_revert`. Changing calibration on real hardware needs a grant naming `output_module.calibrate` with an expiry.
- `CLOCK_IN` device report (ADR 0005, accepted), surfaced as `OutputModuleDriver.clock_in`. Playout is unaffected.
- Optional Descriptor fields `clock_in` and `calibration` under the existing v1 schema.
- Glossary: Ops Lane, Play-on-Arrival.
- ADR 0007 (PROPOSED): play-on-arrival MIDI mode. `beatoven/output_module/arrival.py` holds its MIDI-to-event mapping as a pure function, labelled `NON_DETERMINISTIC`. No device uses it.
- `beatoven.pack.v1` (ADR 0002): `render_pack(..., schema_version="v1")` states the time unit and clock rate and embeds the Output Stream. v0 is still the default and is unchanged.
- `ResonanceFrame.from_source`, a deterministic constructor (ADR 0003).
- Proposed ADRs 0005 (CLOCK IN) and 0006 (calibration commands).
- Decision brief with a recommended answer for every open operator decision (`docs/decisions/`).
- Research pass over the remaining open questions, with each answer checked against its primary source (`docs/decisions/research/open-questions.md`).

### Fixed

- The MIDI port tests no longer crash the whole test run when the operating system refuses to create a MIDI client; they probe in a child process and skip. Before this, 5 of 25 back-to-back runs aborted inside python-rtmidi on macOS.
- A stream could end with the clock jack high when the clock stop fell inside a pulse.
- `infer_era_from_heuristics` returns `unknown` for featureless input (issue #22).

### Removed

- Azure deploy workflow, `render.yaml`, `Dockerfile` and `.azure/`. The API is not hosted.

### Changed

- **Operator decisions of 2026-11-12 applied** (`docs/decisions/applied.md`). Pack times are read as bars. The clock follows tempo at 24 pulses per quarter note and `cv.clock_hz` is no longer used. Keepalive timeout is 300 ms and the driver syncs every 100 ms. A RhythmTokens step fires above 0. These change the default output of `from_pack`, `from_resonance_frame` and `from_audio_control_frames`; pass `time_unit`, `clock_ppqn` or `step_threshold` for the old behaviour.
- **Golden vectors regenerated** (`beatoven/output_module/vectors/`): new `stream_id` `08592ce0…`, trace `ed5f5523…`. The hardware repository must re-vendor them.
- Default look-ahead in the host driver is 100 ms (was 50), after the sync round trip measured up to 48 ms through the OS MIDI stack. **Golden vectors regenerated again** (frame send times change; the jack trace does not).
- Constitution ratified as 1.0.0. ADRs 0002 to 0004 accepted.
- Spec: latency requirement restated as playout error; pitch settling requirement stated.
- CI runs the full test suite and tests the Output Module on Python 3.10, 3.11 and 3.13. The minimum Python is now 3.10; 3.9 is past end of life and cannot be tested on current CI runners.

## [1.1.0] - 2026-11-12

First tagged release. The repository was unarchived on 2026-11-11.

### Added

- Output Stream contract `beatoven.output_stream.v1`: one description of what a device plays, with time in microseconds and CV in microvolts.
- Adapters from the BeatOven Pack, `ResonanceFrame`, `AudioControlFrame`, `cv_gate_map` and `MIDIEventStream.v1`.
- Host driver with clock sync, look-ahead feeding, drift tracking and a played-hash check.
- Simulated Output Module that records a jack trace.
- Connection lifecycle with fail-closed behaviour on timing loss.
- Hardware Lane Grant: hardware control is denied unless an operator supplies a grant file.
- One-way link mode for TRS MIDI.
- Real MIDI port transport, tested through virtual ports.
- `python -m beatoven.output_module` command line.
- Spec, plan, tasks and audit under `specs/001-output-module/`; draft constitution; glossary; ADRs.
- CI job for the Output Module tests, spec traceability and replay check.
- Contributing guide, security policy, issue and pull request templates.

### Changed

- README rewritten. The 2025 README is in `docs/archive/`.
- Package metadata moved to `pyproject.toml`. The version now has one source, `beatoven/__init__.py`. It was `0.1.0` in `pyproject.toml` and `1.0.0` in `setup.py`.
- The Azure deploy workflow runs only when started by hand. It had been failing on every push to `main`.

### Fixed

- `/generate` and `/translate` returned HTTP 500 on NumPy 2.

### Removed

- Compiled Python files that had been committed.
- The unmeasured "<1ms" latency claim.

## [1.0.0] - 2025-12

Never tagged or released. Work up to commit `59312f5`: the modular engine, the dsp.coffee bridge, media intelligence, the mobile UI and the Pack renderer.

[Unreleased]: https://github.com/Zero-State-LLC/BeatOven/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Zero-State-LLC/BeatOven/releases/tag/v1.1.0
