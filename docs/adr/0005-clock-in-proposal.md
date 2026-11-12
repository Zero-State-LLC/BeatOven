# 5. What CLOCK IN does (proposal)

Status: PROPOSED. Nothing in `beatoven.output_stream.v1` or the wire protocol is changed by this document.

## Context

The hardware design has a CLOCK IN jack, and its edges are timestamped in firmware. The contract has no message for it, so the jack has no defined behaviour (`specs/001-output-module/spec.md`, open clarification 4).

Two things pull against each other. A performer expects a clock input to make the Module follow the Rig. SEED determinism (constitution, principles 1 and 2) says the same stream gives the same voltages at the same offsets, which an outside clock would change.

## Proposal

Two steps. Only the first is proposed for acceptance now.

1. **Report only.** The device measures CLOCK IN and tells the host. Playout is unaffected, so determinism is untouched.
   - New device-to-host message `CLOCK_IN` (type `0x47`), body `>QII`: device time of the last rising edge in µs, the period between the last two edges in µs, and a count of edges since sync.
   - Sent at most once per 100 ms, and only while edges arrive.
   - The Descriptor gains `clock_in: true` where the jack exists.
   - The host may use it to choose a tempo before it compiles the next stream. A stream already playing is never changed.
2. **Slaved playout, later.** A mode in which the device stretches stream time to follow CLOCK IN. It would be labelled non-deterministic, as play-on-arrival is, and it needs its own ADR: a pulses-per-quarter-note setting, what happens when the clock stops, and how the played hash is defined.

## Migration

Additive. A host that does not know `0x47` ignores it, as it ignores any unknown type today `[NEEDS CLARIFICATION: confirm the driver ignores unknown device message types rather than failing]`. The golden vectors do not change, because the simulated run has no CLOCK IN edges.

## Open

- `[NEEDS CLARIFICATION: is report-only enough for the first hardware revision, or is slaved playout required?]`
- The 100 ms report interval and the body layout are this proposal's choices; nothing external fixes them.
