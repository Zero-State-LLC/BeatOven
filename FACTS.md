# Facts

Project facts the operator has stated or corrected. Read this first.

- 2026-11-11: BeatOven is built as software in this repo. The hardware is a separate repo (working name Kiln, `Zero-State-LLC/Kiln`).
- 2026-11-11: This repo was unarchived on the operator's instruction. PRs #10–#12 are duplicates and were left as they are.
- "BeatOven" is not "Beatoven.ai". That is an unrelated company.
- PsyFi owns visualization. BeatOven never does.
- Canon (Notion Spine 006 and 009) says `hardware_control_allowed: false`. Code keeps that default. Only an operator grant file opens the hardware lane.
- "Output Module" is a PROPOSED name for the device. It is not the product name.
- 2026-11-12: the operator accepted all 28 recommended answers in `docs/decisions/2026-11-12-operator-decisions.md`. Key ones: Pack times are in **bars**; the clock follows tempo at 24 pulses per quarter note and `cv.clock_hz` is not used; keepalive timeout is 300 ms; a RhythmTokens step is a velocity and fires above 0; iOS is not required for v1; the product will not ship as "Kiln"; the API is not hosted (Azure deploy files removed).
- 2026-11-12: hardware control is allowed by Hardware Lane Grant only. The agent does not write grant files or edit Notion: the operator issues the grant and amends Spine 006 and 009.
- 2026-11-13: **the product name is BeatOven.** The hardware ships under that name; "Output Module (PROPOSED)" stays the term for the device, and "Kiln" stays the hardware repository's name only. Never "Beatoven".
- 2026-11-13: the operator ruled on ADRs 0005 and 0006 (accepted, as amended) and deferred ADR 0007 until after the first hardware revision. The Hardware Lane is about voltage at the jacks, whoever asks for it, and is enforced by the host only.
- 2026-11-13: the operator delegated the remaining open decisions to the agent, to be settled "with docs or research". Those are recorded in `docs/decisions/2026-11-13-delegated-decisions.md`, each marked as the agent's decision so the operator can overturn it. This does not extend to issuing a Hardware Lane Grant, editing Notion, filing applications or closing other people's pull requests.
