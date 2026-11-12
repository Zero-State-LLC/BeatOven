# Tasks: 001-output-module

`[P]` = can run in parallel with its neighbours. `[x]` = done on branch `feat/output-module-contract`, with the test that proves it. Hardware tasks live in the hardware repo.

## Setup

- [x] 001-T001 Unarchive the repo and create the branch
- [x] 001-T002 Write `audit.md` (Gate 0)
- [x] 001-T003 [P] Research: prior art, transport, concept, NVIDIA record (Gate A)
- [x] 001-T004 [P] Write the constitution and the glossary delta
- [ ] 001-T005 Operator rules on the open clarifications in `spec.md`, starting with the Hardware Lane

## Foundational

- [x] 001-T010 Output Stream, Output Event, Output Channel with validation and content address: FR-001, FR-002, FR-003 (workflows: anti-slop-code, production-systems)
- [x] 001-T011 Encode the transitions table and refuse everything else: FR-012 (workflows: anti-slop-code, production-systems)
- [x] 001-T012 [P] Descriptor and quantization rule: FR-004 (workflows: anti-slop-code)
- [x] 001-T013 [P] Wire frame, 7-bit packing, CRC: FR-010 (workflows: anti-slop-code, production-systems)
- [x] 001-T014 [P] Publish the stream schema and the lifecycle JSON: FR-001, FR-012 (workflows: google-developer-style)

## P1: Play a BeatOven Pack the same way every time

- [x] 001-T020 Pack adapter with required time unit, overlap rule, and notes: FR-005 (workflows: anti-slop-code)
- [x] 001-T021 Host driver: enumerate, sync, feed ahead, played-hash check: FR-013, FR-016 (workflows: production-systems, anti-slop-code)
- [x] 001-T022 Simulated Output Module with scheduler and Jack Trace: FR-013, FR-018 (workflows: production-systems, anti-slop-code)
- [x] 001-T023 [P] CLI: compile, simulate, replay-check: FR-002, FR-018 (workflows: anti-slop-code)
- [x] 001-T024 [P] Export golden vectors for firmware: FR-013, FR-016 (workflows: production-systems)

## P2: Fail closed when timing is lost

- [x] 001-T030 Device-side event checks (FR-003) and loss detection (late, gap, integrity, keepalive, sync, overflow, abort) and fail-closed outputs: FR-014 (workflows: production-systems, anti-slop-code)
- [x] 001-T031 No resume without resync: FR-015 (workflows: production-systems)
- [x] 001-T032 [P] Hardware Lane Grant, deny by default: FR-017 (workflows: production-systems, anti-slop-code)

## P3: Bring every existing contract over

- [x] 001-T040 [P] ResonanceFrame adapter: FR-007 (workflows: anti-slop-code)
- [x] 001-T041 [P] AudioControlFrame and cv_gate_map adapters: FR-008 (workflows: anti-slop-code)
- [x] 001-T042 [P] MIDIEventStream.v1 adapter on the PROPOSED event shape: FR-009 (workflows: anti-slop-code)
- [x] 001-T043 Ops lane carried in the new envelope: FR-011 (workflows: anti-slop-code, production-systems)
- [x] 001-T044 Test that the Pack and its schema are untouched: FR-006 (workflows: anti-slop-code)
- [x] 001-T045 Write the Pack v1, ResonanceFrame and MIDIEventStream.v1 proposals as ADRs (`docs/adr/`, status PROPOSED): FR-006 (workflows: google-developer-style)

## P1-HW: The physical Output Module (hardware repo)

- [x] 001-T050 Firmware core in C passing the golden vectors (Kiln `make -C firmware/core test`: 561 checks, trace byte-identical): FR-013, FR-014, FR-016, FR-025 (workflows: anti-slop-code, production-systems)
- [ ] 001-T051 Schematic and layout; ERC and DRC at 0 errors. BLOCKED: KiCad install needs an administrator password: FR-019, FR-020, FR-021, FR-024 (workflows: production-systems)
- [ ] 001-T052 Costed BOM with two sources per active part. PARTIAL: 11 of 32 lines priced: FR-020, FR-021 (workflows: production-systems, google-developer-style)
- [x] 001-T053 Panel drawing with jack and LED coordinates: FR-019 (workflows: google-developer-style)
- [ ] 001-T054 Build boards; run HT-1, HT-2, HT-3, HT-5: FR-020, FR-021, FR-023, FR-024 (workflows: production-systems)
- [ ] 001-T055 Run HT-4 and HT-6 on hardware: FR-022, FR-025 (workflows: production-systems)
- [x] 001-T056 Real MIDI port transport in the host driver, behind the grant, tested over virtual ports: FR-017, FR-027 (workflows: anti-slop-code, production-systems)
- [ ] 001-T057 Measure host-to-jack latency on hardware: FR-022 (workflows: production-systems)

## Polish

- [ ] 001-T090 Converge the code against the spec after the operator's rulings (workflows: anti-slop-code)
- [x] 001-T091 Add a CI job for the Output Module tests, the traceability check and the replay check (workflows: production-systems)
- [x] 001-T092 Fix the API tests that failed on NumPy 2 (workflows: anti-slop-code)
- [ ] 001-T095 Operator decides `test_infer_era_unknown`: the test expects `unknown` for zero sharpness, the code returns `1990s` (workflows: anti-slop-code)
- [x] 001-T093 One-way link mode: FR-026 (workflows: anti-slop-code, production-systems)
- [ ] 001-T096 Plain play-on-arrival MIDI mode, labelled non-deterministic (workflows: anti-slop-code, production-systems)
- [x] 001-T094 README: mark the "<1ms" latency claim as unmeasured and point to this spec (workflows: google-developer-style)
