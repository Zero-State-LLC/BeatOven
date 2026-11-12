# 4. MIDIEventStream.v1 event shape (proposal for canon)

Status: PROPOSED. The Notion schema is unchanged; this repo cannot edit it.

## Context

Canon defines `MIDIEventStream.v1` with `"events": []` and no item shape, a `command_rate_budget` with no unit, and `fail_closed_on_timing_loss` with no behaviour (`specs/001-output-module/audit.md` rows 5 and 9).

## Proposal

1. Event item: `{"t": int, "status": int, "data1": int, "data2": int}`. `t` is ticks for `absolute_tick`, a tick delta for `delta_time`, and microseconds for `wall_clock`.
2. Add `ppq` and `tempo_bpm` to the stream for the two tick modes.
3. Give `command_rate_budget` the unit "messages per second".
4. Define `fail_closed_on_timing_loss` by reference to the Output Module spec: gates low, clock stopped, CV to its Safe Value, no resume without a fresh sync.

## Migration

The adapter `from_midi_event_stream` already reads item 1 and takes item 2 as arguments. If canon adopts a different shape, only that adapter changes.
