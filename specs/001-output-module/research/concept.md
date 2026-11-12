# Concept: the Output Module (PROPOSED)

`[NEEDS CLARIFICATION: product name]` "Kiln" is the hardware repo's working name; no Eurorack product with that name was found (OBSERVED, [prior-art.md](prior-art.md) §4). The name must not be "Beatoven": Beatoven.ai is an unrelated company.

## What it is

A Eurorack Module that plays BeatOven. BeatOven compiles Abraxas Oracle output into an Output Stream: every pitch, gate, trigger, clock edge and modulation voltage, each with a time in microseconds. The Output Module receives that stream over USB, schedules it on its own clock, and plays it out of 3.5 mm jacks into a Rig.

## Who it is for

No source ranks the three candidate groups by size; any ranking is SPECULATIVE ([prior-art.md](prior-art.md) §3). Ranked by fit:

1. **Generative and ambient producers.** They already let a system compose; they want the result to be repeatable so a take can be re-rendered. (INFERRED)
2. **Installation artists.** They need unattended running and a safe state when the computer drops out. (INFERRED from one OBSERVED post about a months-long installation)
3. **Eurorack live performers.** They need tight timing and a safe failure, but many prefer hands-on sequencing. (INFERRED)

Computer-to-modular is an established path: Expert Sleepers lists Max, Reaktor, Bitwig and Ableton CV Tools as hosts for the ES-8 and ES-9 (OBSERVED, prior-art.md §3).

## Core loop

The performer points BeatOven at an Oracle signal and a seed. The Rig starts playing: bass and melody on two pitch outputs, drums on triggers, six voltages moving filters and timbre as the signal's pressure and tension move. The performer patches and turns knobs; the composition comes from the Oracle. Pull the USB cable and every gate drops and the clock stops within one scheduler tick. Run the same seed tomorrow and the same voltages come out at the same microsecond offsets.

## User journeys

1. **Play a run.** Connect, see "synced", press play; the Rig plays the BeatOven Pack.
2. **Replay a run.** Play the same seed twice; the recorded jack traces are identical.
3. **Lose the host.** The laptop sleeps mid-set; outputs fail closed; nothing resumes until the performer re-syncs.
4. **Rehearse without hardware.** Run the same stream on the simulated Output Module and read the jack trace.
5. **Use it as a plain MIDI-to-CV Module.** A DAW sends notes and clock; the Module plays them on arrival, labelled non-deterministic.

## Differentiation

A sequencer plays what a person programmed. A MIDI-to-CV interface plays what arrives, when it arrives. The Output Module differs in four ways:

- **The source is a symbolic signal**, not notes a person entered.
- **SEED determinism reaches the jack**: the stream is content-addressed and the device returns a hash of what it played.
- **Events are scheduled, not played on arrival**, so USB polling jitter (0.61–1.41 ms measured spread, OBSERVED, [transport-facts.md](transport-facts.md) §1.2) does not reach the outputs. (INFERRED; not yet measured on hardware)
- **Timing loss has a defined result**: gates low, clock stopped, CV held or slewed to a safe value.

None of the 26 surveyed products documents content-addressed replay or a defined timing-loss state (INFERRED from prior-art.md; absence in public documentation, not proof of absence).

## Non-goals

- No audio output and no audio synthesis.
- No visualization. PsyFi owns it.
- No on-device generation or ML. The Module plays; BeatOven composes.
- No Wi-Fi.
- No control of other Modules' settings; it emits voltages only.
- No autonomous start: nothing plays without an operator grant and an explicit play.
- Not a replacement for the dsp.coffee bridge types, which stay as they are.
