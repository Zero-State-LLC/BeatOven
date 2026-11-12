# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Schema identifiers such as `beatoven.pack.v0` and `beatoven.output_stream.v1` are versioned on their own and do not follow the package version.

## [Unreleased]

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
