# 5. What CLOCK IN does

Status: ACCEPTED by the operator on 2026-11-13, as amended below. Step 1 is implemented in the reference device and the host driver. Step 2 is not accepted and not built.

## Context

The hardware design has a CLOCK IN jack, and its edges are timestamped in firmware. The contract had no message for it, so the jack had no defined behaviour (`specs/001-output-module/spec.md`, former open clarification 4).

Two things pull against each other. A performer expects a clock input to make the Module follow the Rig. SEED determinism (constitution, principles 1 and 2) says the same stream gives the same voltages at the same offsets, which an outside clock would change.

## Decision

**Report only.** The device measures CLOCK IN and tells the host. Playout is unaffected, so determinism is untouched.

- New device-to-host message `CLOCK_IN` (type `0x47`), body `>QII`: device time of the last rising edge in µs, the period between the last two edges in µs, and a count of edges since the device last entered `SYNCED` from `ENUMERATING` or `SAFE_IDLE`. A repeated sync while already `SYNCED` does not reset the count.
- The device reports the raw period only. It does not know or assume a pulse rate.
- Reports are sent only in `SYNCED` and `STREAMING`, at most once per 100 ms while edges arrive, and only once two edges give a period.
- When 2 s pass with no edge, the device sends one final report with period 0. If the device is in another state at that moment, it sends that report on its next entry to `SYNCED`.
- The Descriptor gains the optional field `clock_in: true` where the jack exists. The field stays under `beatoven.output_module_descriptor.v1`; absent means the device has no CLOCK IN. No Descriptor version bump.
- The host turns a period into a tempo by assuming a pulse rate. The default is 24 pulses per quarter note, the same as the clock output, and it is a host-side setting.
- The measured tempo is **shown and logged only**. It has no path into a render. Tempo is computed from the Oracle (`map_tempo` in `beatoven/engine/render.py`); letting a jack override it would make the Rig an input to the compiler, which is a different decision and needs its own ADR.

## Not accepted: slaved playout

A mode in which the device stretches stream time to follow CLOCK IN. It would not be deterministic, and it needs its own ADR: what happens when the clock stops, and how the played hash is defined.

## Migration

Additive. A host that does not know `0x47` drops the frame and carries on (acceptance test AT-034). A Descriptor without the field still parses. The golden vectors do not change: the recorded run has no CLOCK IN edges.

Kiln's firmware core must add the message and regenerate its Descriptor test fixture, because the reference Descriptor now carries `clock_in` and `calibration`.

## Consequences

- With a sequencer clock patched in, a stream still plays at the tempo it was compiled with and will drift against that sequencer. That is accepted for the first hardware revision.
- The 100 ms interval, the 2 s stop time and the body layout are this ADR's choices; nothing external fixes them.
