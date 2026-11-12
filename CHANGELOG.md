# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Schema identifiers such as `beatoven.pack.v0` and `beatoven.output_stream.v1` are versioned on their own and do not follow the package version.

## [Unreleased]

### Added

- Decision brief with a recommended answer for every open operator decision (`docs/decisions/`).
- Research pass over the remaining open questions, with each answer checked against its primary source (`docs/decisions/research/open-questions.md`).

### Fixed

- A stream could end with the clock jack high when the clock stop fell inside a pulse.
- `infer_era_from_heuristics` returns `unknown` for featureless input (issue #22).

### Removed

- Azure deploy workflow, `render.yaml`, `Dockerfile` and `.azure/`. The API is not hosted.

### Changed

- **Operator decisions of 2026-11-12 applied** (`docs/decisions/applied.md`). Pack times are read as bars. The clock follows tempo at 24 pulses per quarter note and `cv.clock_hz` is no longer used. Keepalive timeout is 300 ms and the driver syncs every 100 ms. A RhythmTokens step fires above 0. These change the default output of `from_pack`, `from_resonance_frame` and `from_audio_control_frames`; pass `time_unit`, `clock_ppqn` or `step_threshold` for the old behaviour.
- **Golden vectors regenerated** (`beatoven/output_module/vectors/`): new `stream_id` `08592ce0…`, trace `ed5f5523…`. The hardware repository must re-vendor them.
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
