# BeatOven

The Oracle-to-music compiler. It turns Abraxas Oracle output into music and into a stream a device can play. It does not visualize; PsyFi does.

## Language

Existing terms keep their meaning and source. This file adds only the terms in the delta table. PatchHive terms (**Rig**, **Case**, **HP**, **Module**, **Placement**) mean what the PatchHive glossary says.

**BeatOven**:
The Oracle-to-music compiler, and the name the product ships under: the compiler together with the Module that plays its output.
_Avoid_: Beatoven, Beatoven.ai (an unrelated company), Kiln (the hardware repository's name only)

**BeatOven Pack**:
The output of one render: MIDI, an optional cv block, a session recipe and provenance.
_Avoid_: bundle, export

**Output Module** (PROPOSED):
The Eurorack Module that plays an Output Stream from its jacks. It is the hardware part of BeatOven.
_Avoid_: interface, converter, the box

**Output Stream**:
The ordered, timed list of everything an Output Module will do for one run.
_Avoid_: event stream, CV stream, MIDI stream

**Output Event**:
One change at one Output Channel at one time.
_Avoid_: message, command

**Output Channel**:
One signal an Output Module produces, named by what it carries and a number.
_Avoid_: lane (that is the Pack's word), voice, port

**Descriptor**:
An Output Module's own statement of which Output Channels it has and what each can do.
_Avoid_: capabilities, profile

**Jack Trace**:
The record of every change at every jack during a run, with its time.
_Avoid_: capture, log

**Hardware Lane**:
The permission to drive a physical device.
_Avoid_: hardware mode

**Hardware Lane Grant**:
An operator's written permission that opens the Hardware Lane for a named scope.
_Avoid_: token, key

**Ops Lane**:
The path for commands to a device that are not Output Events.
_Avoid_: control channel, command stream

**Play-on-Arrival** (PROPOSED):
A device playing plain MIDI as it arrives, with no Output Stream. Not deterministic.
_Avoid_: live mode, MIDI mode, passthrough

**Timing Loss**:
The moment a device can no longer play the Output Stream at its stated times.
_Avoid_: dropout, glitch, underrun

**Safe Value**:
The level an Output Channel takes after Timing Loss.
_Avoid_: default, zero

## Delta table (added 2026-11-11 by specs/001-output-module)

| Term | Source | Reason it is needed |
|---|---|---|
| Output Module (PROPOSED) | fable prompt §1; operator instruction 2026-11-11 | The hardware had no name. Stays PROPOSED until the spec names it. |
| Output Stream | audit row 2 | Four contracts each described "what goes to hardware"; one word was needed for the single canonical thing. |
| Output Event | audit row 2 | The unit of an Output Stream. "Event" alone collides with MIDI events and lifecycle events. |
| Output Channel | audit row 3 | The Pack says "lane" for a list of points. A physical signal with a range is a different thing. |
| Descriptor | spec FR-004 | The host must not guess what a device can do. |
| Jack Trace | spec FR-018 | The thing two replays are compared by. |
| Hardware Lane, Hardware Lane Grant | audit row 1; Spine 006 and 009 `hardware_control_allowed` | Canon forbids hardware control; a bounded exception needs a name. |
| Ops Lane | dspcoffee bridge `ops` commands; ADR 0006 | The word was in use for the command path without a definition. "Lane" otherwise stays the Pack's word. |
| Play-on-Arrival | concept journey 5; ADR 0007 | Used in four documents and the code with no entry. |
| Timing Loss | MIDI Batch 003 `fail_closed_on_timing_loss` | Canon used the phrase without defining it. |
| Safe Value | spec FR-014 | "Fail closed" needs a stated end state per Output Channel. |
