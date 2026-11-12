# Decisions waiting on the operator, with a recommended answer for each

Date: 2026-11-12. Nothing here is decided. Each row gives the answer I would pick, why, and the next-best option.

Sources are in [research/](research/): `decisions-parts.md` (P), `decisions-conventions.md` (C) and `decisions-remaining.md` (R, gathered through context.dev) and `open-questions.md` (Q, a second pass that checked each answer against the primary document). The hardware review is in the Kiln repository, `docs/rev-a-review-fixes.md`. Labels: OBSERVED (read in a cited source), INFERRED (reasoned), SPECULATIVE.

To answer, reply with the row numbers you accept and your own answer for the rest.

## A. Authority and canon (no research can settle these)

| # | Decision | Recommended answer | Why | Next-best |
|---|---|---|---|---|
| A1 | Hardware lane authority (issue #18) | Amend Spine 006 and 009 to say hardware control is allowed **by Hardware Lane Grant only**, and issue one grant scoped to `output_module` for prototype work. | Code already enforces deny-by-default with a scoped grant. Canon and code would then agree. | Leave canon as it is and issue a time-limited grant per bench session. |
| A2 | Ratify the constitution (issue #21) | Ratify as 1.0.0 once A1 is settled; principle 7 depends on it. | It restates rules already in canon plus the grant rule. | Ratify without principle 7. |
| A3 | ADRs 0002 to 0004 (issue #20) | Accept all three, with 0002 amended by B1 and B2 below. | Each is additive and leaves v0 readable. | Accept 0003 and 0004 only. |
| A4 | PRs #10 to #12 (issue #26) | Close #10 and #11 as duplicates. Keep #12 open until someone checks it against today's `main`. | The three carry near-identical work from 2025-12. | Close all three. |
| A5 | Azure deploy workflow (issue #27) | Delete the workflow, `render.yaml` and the Dockerfile unless the API is meant to be hosted. | It has no credentials and failed on every push. | Keep it manual-only, as now. |

## B. The contract (BeatOven)

| # | Decision | Recommended answer | Why | Next-best |
|---|---|---|---|---|
| B1 | Unit of the Pack's `t` and `dur` | **Bars.** | OBSERVED in `beatoven/engine/mapping.py:90-93`: the controller lane puts points at `0`, `bars / 2` and `bars`. I had inferred beats; the code says otherwise. Consequence: regenerate the golden vectors with `--time-unit bars` and re-vendor them in Kiln. | Beats, with the controller lanes treated as a bug. |
| B2 | Does `cv.clock_hz` follow tempo? | **Yes.** Derive the clock from `tempo_bpm` and a stated pulses-per-quarter-note value; drop the free-running `clock_hz`. | The Abraxas overlay already computes its clock from tempo (OBSERVED, `Abraxas/abraxas/overlays/beatoven.py:33`). Two unrelated clocks cannot both be right. | Keep `clock_hz` as a separate modulation rate and rename it. |
| B3 | Default clock rate | **24 pulses per quarter note**, configurable. | A-190-4 follows MIDI clock at 24; Pamela's Workout defaults to 24; BeatStep Pro offers 24, 48, 2 and 1 (OBSERVED, R§11). | 4 per quarter note (one per sixteenth), which many analogue sequencers expect. |
| B4 | Which note is 0 V | **C0, MIDI note 12**, configurable per stream. | There is no single convention: FH-2 puts note 60 at 0 V on a ±5 V output, Yarns uses note 36, A-190-4 defaults to note 24, uMIDI uses note 0 (OBSERVED, R§5). The original acceptance test is "C0 to C5 over 5 octaves", which reads most naturally with C0 at 0 V. | Note 24, the Doepfer A-190-4 default. |
| B5 | Pitch output range | **0 to +10 V, fixed.** | BeatStep Pro and uMIDI use 0 to 10 V (OBSERVED, R§5). One unipolar precision stage is the simplest to calibrate. BeatOven's notes (36 to 71) sit at 2.0 to 4.9 V. | −3 to +7 V, as Yarns calibrates (OBSERVED, C§4). |
| B6 | Modulation output range | **−5 to +5 V hardware, with 0 to +5 V as the default mapping.** | FH-2 offers ±5 V and 0 to 5 V among its ranges (OBSERVED, R§5). Bipolar hardware covers both. | 0 to +8 V, the Doepfer envelope range. |
| B7 | Gate level | **+5 V.** | Doepfer: 0 / +5 V typical, high above about +3 V, inputs tolerate up to +12 V (OBSERVED, R§11). | +10 V by jumper, for older gear that needs it. |
| B8 | Trigger length | **5 ms default, 1 ms minimum, configurable.** | No published standard was found (R§11). 5 ms is my choice; the 1 ms floor is from the original brief. | 10 ms default. |
| B9 | Safe Value policy and timeout | Gates, clock and reset low at once; **pitch holds; modulation slews to 0 V in 50 ms**. Shorten the keepalive timeout from 500 ms to **300 ms**. | The MIDI 1.0 active-sensing rule is 300 ms (OBSERVED, C§7). Doepfer A-190-4 turns the gate off and holds CV on All Notes Off (OBSERVED, R§8). No comparable product documents an automatic host-loss timeout, and the 50 ms slew has no precedent; it is my choice. | Hold every CV, gates low. |
| B10 | Step values and swing in `RhythmTokens` | A step value is a **velocity**; a step fires when it is above 0. Leave swing out of what reaches hardware until it has a definition. | Matches ADR 0003. | Keep the required `step_threshold` argument, as now. |
| B11 | Is iOS a required host? | **Not for v1.** Test on an iPad afterwards. | Apple documents that MIDI interfaces work through its adapters and warns about power draw, but gives no current figure; one developer reports dropped MIDI after SysEx on iOS (OBSERVED, R§7). The design is self-powered, which helps. | Require it, and add an iPad to the bench plan. |
| B12 | `test_infer_era_unknown` (issue #22) | **Change the code**: return `unknown` when both features are near zero. | The test was written with the function and has failed since. "Unknown remains unknown" is in the constitution. | Change the test. |

## C. The hardware (Kiln)

| # | Decision | Recommended answer | Why | Next-best |
|---|---|---|---|---|
| C1 | LED mounting | **Flat-top 3 mm through-hole LEDs on long legs, soldered with the panel fitted.** Put each LED in the gap above its jack and widen the row pitch from 16.0 to **18.5 mm**. Keep the 12.70 mm column pitch. | Measured from the project's own footprints: the jack courtyard is 9.5 x 13.85 mm and the LED's is 4.84 x 4.42 mm, so rows need at least 18.3 mm (INFERRED from OBSERVED footprint geometry). Four rows then span 55.5 mm, which fits. Music Thing's Turing Machine and Workshop System mount LEDs this way (OBSERVED, P§1). The jack body is about 10 mm tall (OBSERVED from two sources; one lists 9 mm, R§1). | Surface-mount LEDs on the back with Bivar GVLP light pipes, after a sample fit. |
| C2 | Final HP | **12 HP.** | ES-8 puts 12 jacks in 8 HP and ES-9 puts 25 in 16 HP (OBSERVED, P§3); 16 jacks in 12 HP is in line. | 14 HP, if C1's taller grid feels cramped next to the USB port. |
| C3 | USB-C part | **GCT USB4145-03-0170-C**, vertical, 16 contacts, 7.46 mm tall, with the panel cutout sized for the plug's overmold (at least 12.5 x 7 mm). **Mock it up before ordering boards.** | It carries D+/D− and was in stock (OBSERVED, P§2, R§3). With a 10 mm board-to-panel gap its mouth sits about 4.5 mm behind the panel face (INFERRED). USB-IF allows the plug's overmold seat up to 6.5 mm from the receptacle datum (OBSERVED, R§3), so a plug reaches only if the cutout admits the overmold. GCT's mating drawing confirms it: a mated cable plug's overmold sits 9.66 mm above the board, 2.3 mm below the outer face of a 2 mm panel on a 10 mm gap (OBSERVED drawing, INFERRED fit, Q§2). | A small front board carrying the socket, as Winterbloom's Sol does for its USB-B (OBSERVED, R§2). |
| C4 | Autorouter | **Allow Freerouting 2.5.0 for low-speed digital nets only.** Hand-route USB, the 1.1 V supply, every analogue net and power. | GPL-3.0, released 2026-10-05 with a checksum per file; runs headless (OBSERVED, C§1). KiCad forum moderators advise against trusting an autorouter on mixed-signal boards (OBSERVED, forum only). It needs installing; that is your call. | Route everything by hand in KiCad. |
| C5 | Pitch accuracy requirement | Replace "settle in 10 µs to half an LSB" with: **static error within ±0.5 mV at every calibration point, and a 1 V step within 1 cent (833 µV) inside 200 µs, measured at the jack.** Keep "±1 cent per octave over 5 octaves after calibration". | No 16-bit DAC states the original figure; the DAC80508 states 5 µs to ±2 LSB, which is ±0.37 cent on a 10 V span (OBSERVED datasheet, INFERRED arithmetic, R§14). The smallest pitch step people hear is about 3 to 6 cents at 1 to 2 kHz (OBSERVED, Kunchur 2023, R§12). The thresholds are my proposal; they are testable with a 6.5-digit meter and a scope. | Keep the datasheet figure as the requirement: 5 µs to ±2 LSB, by citation only. |
| C6 | Latency requirement | Restate "2 ms p99 from host send to jack" as **playout error: each event within 100 µs RMS of its scheduled time**, plus a stated minimum lead of 5 ms. | Events are sent 20 to 70 ms early on purpose, so send-to-jack latency is the look-ahead, not a fault. | Keep 2 ms for the play-on-arrival mode only. |
| C7 | Power header | **Shrouded 2 x 5 header**, −12 V marked on the silkscreen, series Schottky on both rails. | Doepfer's FAQ says it moved its own bus boards to boxed headers in 2019 (OBSERVED, C§3). Winterbloom's Sol fits a shrouded 2 x 5 with two protection diodes (OBSERVED, R§4). A shroud cannot protect against a cable built backwards, so the diodes stay. | Unshrouded 2 x 5 with the same diodes. |
| C8 | Do the 120 mA and 50 mA limits cover faults? | **Normal operation only.** Record the all-outputs-shorted case separately (calculated 174 mA and 189 mA) with its own limit. | Normal draw is calculated at 51.7 and 20.5 mA, using datasheet op-amp and DAC currents (Q§7); the earlier 40.8 and 11.3 mA used placeholder allocations. | Make the limits cover faults and add a current limiter per rail. |

## D. Identity and naming

| # | Decision | Recommended answer | Why | Next-best |
|---|---|---|---|---|
| D1 | USB vendor and product ID | Request a product ID under Raspberry Pi's vendor ID `0x2E8A`. | Raspberry Pi sub-licenses product IDs for RP2040 and RP2350 products, lists commercial ones including RP2350 products, and mentions no fee. It asks applicants whether a standard class device needs its own ID at all, and a reserved ID is lost if it is not listed publicly at launch (OBSERVED, Readme read directly, Q§1). A USB-IF vendor ID alone costs US$6,000 (OBSERVED, C§5). | pid.codes, free but open hardware only. |
| D2 | MIDI SysEx manufacturer ID | Keep `0x7D` for prototypes. **Buy a MIDI Association ID before anything ships** (US$240 one time). | `0x7D` may not be used in a product released to the public (OBSERVED, C§5). | Ship open source only and stay on `0x7D` for kits, which is a grey area. |
| D3 | Product name | **Do not ship as "Kiln".** Keep it as the repository's working name and pick another product name. | Vitric Audio sells a wavetable synthesizer plugin called "Kiln Synthesizer", reported in September 2026 (OBSERVED, R§9). No Eurorack hardware named Kiln was found. One US application for KILN exists (serial 99654583, filed 2026-02-16, a fitness-training app, office action pending), read on a third-party mirror of USPTO data; it is not for music or electronics (OBSERVED, Q§1). EUIPO and UKIPO were not searched. This is a findability report, not legal advice. | Use "Kiln" with a qualifier after a manual trademark search. |

## What research could not settle

- The jack's height: two sources say 10 mm and one says 9 mm. A retailer listing explains the gap as a 1 mm seating tab (reported by a tool, not confirmed). A calliper on a real part settles it, and C1 and C3 both depend on it.
- How Expert Sleepers, monome, Intellijel and others mount a front-panel USB socket.
- What Mutable, Intellijel and Make Noise fit as power headers.
- Apple's numeric power limit for USB accessories.
- Any "Kiln" record at EUIPO or UKIPO, and a direct USPTO search.
- Which pad the core-supply inductor's polarity dot faces, and the RP2350's run current.
- The price of the bare board.

## Corrections to earlier statements

- Kiln's power budget used placeholder currents for the op-amps. With datasheet figures, normal draw rises from 40.8 to 51.7 mA on +12 V and from 11.3 to 20.5 mA on −12 V, still inside the limits (C8).
- The audit and spec say the Pack's time unit is "beats (INFERRED)". The code supports bars (B1).
- An earlier summary gave one cent as 0.083 mV. It is 0.833 mV.
- The first LED recommendation was light pipes. Published designs and the footprint geometry favour long-leg LEDs with wider rows (C1).
