# Decisions of 2026-11-13

Two kinds of decision are recorded here, and they are kept apart.

- **Operator:** stated by the operator on 2026-11-13.
- **Agent, under delegation:** the operator said "handle the rest of the decisions with docs or research". Each of these is the agent's decision, with the evidence it rests on. The operator can overturn any of them; none is hard to reverse.

Labels OBSERVED, INFERRED and SPECULATIVE are used as elsewhere. "Read" means the primary source was fetched and the text matched on 2026-11-13.

## 1. Operator

| # | Decision |
|---|---|
| 1 | **The product name is BeatOven.** The hardware ships under that name. "Output Module (PROPOSED)" stays the term for the device; "Kiln" stays the hardware repository's name. |
| 2 | ADR 0005 (CLOCK IN, report only) and ADR 0006 (calibration commands, no `CAL_RAW`, separate expiring grant scope) are accepted as amended. ADR 0007 (play-on-arrival) is deferred until after the first hardware revision. |
| 3 | The Hardware Lane is about voltage at the jacks, whoever asks for it. It is enforced by the host only. |

## 2. What the name decision runs into

These are facts for the operator, not a legal opinion. No lawyer has looked at this.

| Fact | How known |
|---|---|
| **BEATOVEN is a live US registration.** Serial 97546085, registration 7363061, registered 2024-04-23, Principal Register, service mark. Owner: Beatoven Private Limited, Bengaluru, India. Class 41: "Music composition services". Class 42: platform and software as a service "using artificial intelligence to create and edit music and sounds". No goods in class 9 or 15. | Read, USPTO TSDR |
| **BEAT OVEN is a registered UK mark.** UK00004182558, filed 2025-04-01, entered 2025-06-27, owner an individual in London. Class 9 on the register is music recordings and downloadable music. A search tool also listed classes 25 and 41 for it; those were not read on the register. | Read, UKIPO register (class 9 and status); the other classes unconfirmed |
| Beatoven.ai's consumer service was reported discontinued in August 2026, with the company keeping its intellectual property. | One news article; not confirmed |
| No BEATOVEN or BEAT OVEN mark was found at the EUIPO, and none in class 15 anywhere. | Search tool over TMView only; the India and WIPO registers were not searched |
| No hardware, plugin or app sold as "BeatOven" was found. App stores and second-hand markets were not checked. | Web search |

What follows (INFERRED):

- The hardware, a Eurorack Module, is in classes the US mark does not cover.
- The software is closer. BeatOven's compiler turns Oracle data into music, and the US mark covers software services that create music. The names differ only in one capital letter. This is the part a trademark lawyer should look at before any public launch.
- In the UK, the registered BEAT OVEN mark covers music recordings, not instruments or software, on the class read.

**Agent's decision:** the name is used as the operator decided. Before anything is sold or announced publicly, the operator should get a trademark lawyer's view on the US mark. Nothing in the repositories depends on the outcome; a later rename is a text change.

## 3. Agent, under delegation

### 3.1 USB product ID

- **Decision:** apply to Raspberry Pi for a product ID under vendor ID `0x2E8A` once a production start date is known. The operator files it: the form asks for the company's legal name, address, a contact and an email.
- **Evidence (read, `raspberrypi/usb-pid` Readme, updated 2026-11-09):** the form also asks for a product name, purpose, description and link, an estimate of annual usage and of the production start date. The company name, description and link become public. An ID reserved before launch must be added to the public table at launch or it is lost. No fee is stated. Raspberry Pi notes that a separate ID is mainly needed for a vendor-specific Windows driver, so it may suggest a standard one for a class-compliant MIDI device. The form's wording names the RP2040; whether an RP2350 product qualifies is not stated there, though the earlier pass found RP2350 products in the table.
- **Alternatives rejected:** pid.codes is free but requires open-source hardware and firmware, and the hardware repository is private (read, pid.codes). A USB-IF vendor ID costs about US$6,000 (search snippet only).

### 3.2 MIDI manufacturer ID

- **Decision:** buy the MIDI Association's SysEx-only ID before anything ships. Prototypes stay on `0x7D`. The operator files it, since it needs payment and company details.
- **Evidence (read, MIDI Association policy of 2025-10-15):** a paid SysEx ID holder pays US$240 once; corporate membership starts at US$600 a year and includes an ID. `0x7D` "is not to be used on any product released to the public". `0x7C` may be used on a public product only if it earns nothing, so it does not fit either.
- **Not found:** whether a new ID is one byte or three. The wire format (`wire.py`) reserves one byte today; a three-byte ID would change the frame header and needs an ADR when the ID is known.

### 3.3 Spec clarifications

- **Swing in RhythmTokens is a metric, not a timing instruction.** The adapter never moves a trigger because of it; it can be routed to a mod CV like any other metric. Evidence (OBSERVED, code): `swing` is a field of `ResonanceMetrics`, a number from 0 to 1 beside `groove` and `energy`; a RhythmTokens grid has an arbitrary number of steps, so "the off-beat eighth" is not defined for it; the repository's own rhythm engine applies swing before events exist (`beatoven/core/rhythm`). No code changes: the adapter already behaves this way and already notes it in the stream.
- **`BeatOvenRun.v1`**, in this repository, means one render: a BeatOven Pack and the Output Stream compiled from it, identified by the stream id. No schema of that name is defined here. Canon names it without defining it (audit row 9); defining it is canon's job.
- **`MIDIEventStream.v1`** item shape is the one in ADR 0004, already accepted.

### 3.4 Pull request #12 (issue #26)

- **Finding (OBSERVED):** it is not a duplicate. 55 of its 59 files do not exist on `main`. It conflicts with `main` in two files, adds two public API routes with no ADR, and adds `beatoven/engines/` and `beatoven/schema/` beside the existing `beatoven/engine/` and `beatoven/schemas/`. Its own 3 tests pass in a trial merge. Nothing on `main` refers to ABX-Runes.
- **Decision:** do not merge it. Recommend closing it and keeping the branch.
- **Not done:** the agent's attempt to close it was refused by the permission system, so it is still open, with the finding posted on it. Closing it is left to the operator.

### 3.5 Hardware Lane (issue #18)

- **Decision:** none; this is the operator's. Wording for the Spine amendment and two unsigned grant drafts are in [hardware-lane-drafts.md](hardware-lane-drafts.md).

## 4. Hardware facts found on 2026-11-13

These go to the Kiln repository's `docs/research/hardware-facts.md` as well.

| Question | Answer | How known |
|---|---|---|
| RP2350 run current | Datasheet table "Power Consumption" (section 14.9.7.3): running `hello_usb`, 14.7 mA into the regulator input at 3.3 V, 52.7 mW in total. Single-core CoreMark at 150 MHz: 11.0 mA, 38.7 mW. No row for both cores. | Reported by a research agent that read the PDF; not re-read |
| Inductor polarity | The datasheet says the inductor "must be marked for polarity" and placed as its figure shows. The text never names the pad. The figure puts the dot at the end marked "−", with current flowing from "+" to "−". INFERRED: the dot faces the output capacitor, not the switch pin. Kiln copies the placement from Raspberry Pi's own board file, which is the thing to check. | Same; the inference is the agent's |
| Jack height | The Thonkiconn drawing shows 5.5 mm of bushing, a 9 mm body and a 4.5 mm dimension, with no single "board to panel seat" label. Still a calliper measurement. | Same |
| Apple accessory power | "iPhone 15 and later" can supply a USB Power Delivery device "at up to 4.5 watts". No figure in milliamps and none for iPad. This reverses the 2026-11-12 note, which rejected 4.5 W because the page then cited did not contain it. | Read, Apple Support 105099 |

## 5. Still open after this pass

- A lawyer's view on the name (section 2), and searches of the India and WIPO registers.
- Whether Raspberry Pi issues product IDs for RP2350 products, and how long it takes.
- Whether a new MIDI manufacturer ID is one byte or three.
- How other makers mount a front-panel USB socket: no build document or board photo was found for any module.
- The price of the bare board: both order forms were unreadable without a browser session.
- The jack height on a real part.
