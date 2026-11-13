# 7. Play-on-arrival MIDI mode (proposal)

Status: PROPOSED, and deferred by the operator on 2026-11-13: play-on-arrival is not part of the first hardware revision. It will be decided after a board has played an Output Stream on the bench. Nothing in `beatoven.output_stream.v1`, the Descriptor or the wire protocol is changed by this document. The mapping below exists as a pure function in `beatoven/output_module/arrival.py`; no device, simulated or real, uses it yet.

## Context

Journey 5 in `specs/001-output-module/research/concept.md` says a DAW can send plain notes, CC and clock to the Output Module (PROPOSED) and have it play them on arrival. Task 001-T096 and issue #23 track it.

Three things have to be settled before a device may do this.

1. **Authority.** Spec FR-017 closes the Hardware Lane unless a Hardware Lane Grant names the scope. The grant is checked by the BeatOven host driver. A DAW is not that driver: a device that plays whatever notes arrive moves real voltages with no grant in the path. AGENTS.md forbids adding a way around the grant, so this mode cannot simply be on.
2. **Determinism.** Events are played when they arrive, so USB polling jitter (0.61 to 1.41 ms measured spread, OBSERVED, `research/transport-facts.md` §1.2) reaches the jacks, and two runs differ. There is no stream id, no played hash and no replay check.
3. **Fail closed.** A DAW sends no keepalive. If the host stops, a held note stays held.

## Settled on 2026-11-13

- The Hardware Lane is about voltage at the jacks, whoever asks for it. A DAW driving the device is therefore inside its concern, not outside it.
- The grant is enforced by the BeatOven host only; the device does not verify one (ADR 0006, Authority). How a grant could cover a device acting on its own is not designed.
- The held-note timeout and a configurable mapping are parked with the mode. They are not decided.

## Proposal

### A. Authority: off by default, armed under a grant

- The device ships with play-on-arrival **off**. With it off, channel-voice and real-time MIDI messages are ignored, as they are today.
- It is armed by an Ops command, `ARRIVAL_ARM`, legal only in `SYNCED`, sent by the BeatOven host driver, which requires a Hardware Lane Grant to connect to real hardware. The device stores the setting. `ARRIVAL_DISARM` clears it.
- The Descriptor gains `arrival: "armed" | "off"` where the firmware supports the mode, so a host can see the state.
- `[NEEDS CLARIFICATION: is a stored arming, set once under a grant, an acceptable use of the Hardware Lane Grant, or must the mode stay off until Spine 006 and 009 say otherwise? This is the operator's ruling; the agent does not decide it.]`

### B. Precedence

An Output Stream always wins. Play-on-arrival acts only while the lifecycle is `DISCONNECTED` or `SAFE_IDLE`. From `ENUMERATING` onwards plain MIDI is ignored, and entering `ENUMERATING` first puts every jack at its Safe Value.

### C. Mapping

These are this proposal's choices. Where an operator decision of 2026-11-12 applies, it is used: 0 V is MIDI note 12, mod CV is 0 to +5 V, a trigger is 5 ms, the clock is 24 pulses per quarter note.

| MIDI | Jack | Behaviour |
|---|---|---|
| Notes, channel 1 | `PITCH_CV:0`, `GATE:0` | Monophonic, last note wins. Pitch is 1 V per octave. The gate stays high while any note is held; releasing the newest note returns to the previous held one. Notes that would fall outside the jack's range are ignored. |
| Notes, channel 2 | `PITCH_CV:1`, `GATE:1` | The same, second voice. |
| Pitch bend, channels 1 and 2 | that voice's pitch | ±2 semitones. |
| Note 36, channel 10 | `GATE:2` | 5 ms trigger on note-on. |
| Note 38, channel 10 | `GATE:3` | 5 ms trigger on note-on. |
| CC 1, 2, 16, 17, 18, 19, channel 1 | `MOD_CV:0` to `MOD_CV:5` | Value 0 to 127 maps to 0 to +5 V. |
| CC 120, CC 123 | that voice's gate | Gate low, held notes forgotten. |
| Timing clock (`F8`) | `CLOCK:0` | One pulse per message, so 24 per quarter note. Width 5 ms, or half the interval when messages are less than 10 ms apart, never under 1 ms. |
| Start (`FA`) | `RESET:0` | 5 ms pulse. |
| Stop (`FC`), System Reset (`FF`) | all gates | Low, held notes forgotten. |
| Velocity, aftertouch, program change, SysEx that is not ours | none | Ignored. |

### D. Fail closed, as far as plain MIDI allows

- USB suspend or detach puts every jack at its Safe Value.
- If the host has ever sent Active Sensing (`FE`), 300 ms without any MIDI byte puts the gates low. This is the MIDI 1.0 rule, and it equals the contract's keepalive timeout.
- If the host never sends Active Sensing, a held note stays held until note-off. `[NEEDS CLARIFICATION: is that acceptable, or should an armed device also time out gates after a stated period of silence?]`

### E. Labelling

- The mode is named play-on-arrival and is marked `NON_DETERMINISTIC` in the Descriptor field, the driver's report and the documentation. It produces no stream id and no played hash, and the replay check does not apply to it.
- A front-panel indication while the mode is acting is a hardware question for the Kiln repository.

## What exists now

`beatoven/output_module/arrival.py` holds `ArrivalMapper`: MIDI bytes and an arrival time in, a list of `OutputEvent` out, using table C. It is pure, drives nothing and needs no grant, like the adapters. Its tests are in `beatoven/output_module/tests/test_arrival.py`. It fixes the mapping so the firmware can be checked against it later; it is not the mode.

## Migration

Additive. No existing name, schema or vector changes. If accepted: the Ops kinds and Descriptor field are added, the simulated device gains the mode behind arming, and Kiln's firmware follows.

## Open

- The two `[NEEDS CLARIFICATION]` markers above.
- The channel and controller numbers in table C are choices, not findings. `[NEEDS CLARIFICATION: should they be configurable, and stored where?]`
- Jitter at the jack in this mode has not been measured on any hardware.
