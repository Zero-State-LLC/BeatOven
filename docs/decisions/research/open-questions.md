# Open questions: research pass of 2026-11-12

Scope: every `[NEEDS CLARIFICATION]` in BeatOven and Kiln that a public source could answer, plus the "could not settle" list in the [decision brief](../2026-11-12-operator-decisions.md).

Method: 27 questions were put to context.dev's answer service. Its answers were then checked against the primary document where one could be fetched. Several answers were wrong, so each row says how the fact is known:

- **read**: I matched the text or drawing in the fetched primary document.
- **tool**: the answer service reported it with a source; I did not confirm it.
- **rejected**: the answer was checked and is wrong or unsupported. It is listed so it is not reused.

Labels OBSERVED, INFERRED and SPECULATIVE are used as elsewhere.

## 1. Closed

| # | Question | Answer | How known |
|---|---|---|---|
| 1 | DAC80508 SPI mode (Kiln fix 7) | "SDI data are clocked on SCLK falling edges"; 24-bit frame, 32 with CRC. The firmware's CPOL 0 / CPHA 1 setting matches. OBSERVED | read, TI SLASEL1 section 8.4.1 |
| 2 | DAC80508 supply current | 5 mA typ, 6 mA max with the internal reference on and outputs unloaded; VIO 2 µA typ. OBSERVED | read, section 7.5 |
| 3 | DAC80508 reference drive | ±5 mA load, 100 µV/mA load regulation. OBSERVED | read, section 7.5 |
| 4 | OPA4172 quiescent current | 1.6 mA typ, 1.8 mA max per amplifier at 25 °C. OBSERVED | read, TI SBOS618I |
| 5 | OPA4172 short-circuit rating | ±75 mA; "Continuous" only for a short to ground with one amplifier per package. OBSERVED | read, section 7.1 note 4 |
| 6 | Crystal specification | ABM8-272-T3: ±30 ppm tolerance, 50 Ω maximum ESR, 10 pF load. OBSERVED | read, Raspberry Pi "Hardware design with RP2350" |
| 7 | Typical Eurorack input impedance | Mutable Instruments: "100k input impedance guaranteed" for its CV input stage. No figure found from Doepfer. OBSERVED for one maker | read, pichenettes.github.io `tech_notes/cv_inputs` |
| 8 | Raspberry Pi product ID terms (D1) | Sub-licensed under vendor ID `0x2E8A`; apply through a form; a reserved ID must be added to the public list at launch or it is lost. Raspberry Pi asks applicants to consider whether a separate ID is needed at all for a standard class driver. The list has a "Commercial" range and RP2350 products in it. No fee is mentioned. OBSERVED | read, `raspberrypi/usb-pid` Readme |
| 9 | "KILN" trademark (D3) | A US application exists: serial 99654583, word mark KILN, Fieldhouse Athletic LLC, filed 2026-02-16, status "non-final office action issued" as of 2026-06-15. Goods: a fitness-training mobile app, fitness training services and fitness software as a service. It is not for music or electronics. OBSERVED on a third-party mirror of USPTO data | read, trademarkelite.com |
| 10 | USB4145 mating geometry (C3) | See section 2. OBSERVED | read, GCT drawing sheet 3 |
| 11 | Stereo jack footprint | A community KiCad footprint for the WQP-WQP419GR exists with pads named T, R and S. OBSERVED that it exists; not compared with Kiln's footprint | read, `dchwebb/Custom_Footprints.pretty` |
| 12 | 5 V LDO candidate | LP2985-50: recommended input to 16 V, 150 mA, fixed 5.0 V available. OBSERVED. It works from +12 V with 4 V of margin | read, TI SLVS522 |

## 2. The USB-C connector against the panel (decision C3)

Read from sheet 3 of the GCT USB4145 drawing, "Plug and Receptacle Mating View" (OBSERVED):

- The receptacle is 7.46 mm tall: 2.81 mm from the board to a datum, then 4.65 mm to the mouth.
- With a cable plug mated, the plug's overmold face sits 6.85 mm above the datum, which is 9.66 mm above the board and 2.2 mm above the receptacle's mouth.
- For GCT's own board-mounted plug, a panel on the plug side must be at least 6.55 mm above the datum.

Applied to Kiln (INFERRED): with a 10 mm gap between board and panel and a 2 mm panel, the panel's inner face is 10.0 mm above the board and its outer face 12.0 mm. The overmold has to reach 9.66 mm, so it must pass right through the panel, 2.3 mm below the outer face. The plug therefore mates only if the cutout admits the overmold. The brief's C3 already says this; the drawing confirms it and gives the number.

The answer service's reading of "4.60 max" as a panel distance is **rejected**: on the drawing 4.60 is the contact engagement depth next to 4.65.

Taller vertical parts named by the service (Molex 2193200001 at 8.8 mm, HRO TYPE-C-31-M-33 at 8.94 mm) are **tool** only; no drawing was read. A part 9.5 mm or taller would let the shell reach the panel without the overmold entering it.

## 3. Reported by the tool, not confirmed

| Question | Reported answer | Source it named |
|---|---|---|
| W25Q32JV current | 8 mA typ, 15 mA max reading at 50 MHz; 10 µA typ standby | Winbond W25Q32JV rev J |
| 74AHCT541 input threshold | VIH 2.0 V min at 4.5–5.5 V; ±8 mA output; rise about 3.5 ns | Nexperia 74AHC_AHCT541 |
| TRS MIDI Type A pins | Tip = DIN pin 5 (sink), ring = DIN pin 4 (source), sleeve = shield. Kiln's wiring matches this | MIDI Association RP-054 (the pin table is a drawing I could not read) |
| Jack height (PJ398SM) | 10 mm from board to panel seat; the 9 mm figure excludes a 1 mm seating tab | exploding-shed.com listing |
| Flat-top LED forward voltage | Kingbright WP424: green 2.0 V typ at 10 mA, red 1.85 V typ at 20 mA; no figure at 1 mA | Kingbright datasheets |
| Yarns pitch range | −3 V to +7 V | Yarns manual, calibration |
| KeyStep Pro 0 V note | set by a "Base Note" option | KeyStep Pro manual |
| Host-loss behaviour of other products | none of FH-2, Yarns or A-190-4 documents an automatic gate-off when the host stops | their manuals |
| Trigger lengths | Mutable Grids 1 ms; Doepfer A-165 about 50 ms; no maker publishes a minimum detectable width | Grids and A-165 manuals |
| iOS SysEx | one developer report of malformed USB-MIDI packets and dropped messages after SysEx since iOS 16; no Apple-documented size limit | developer.apple.com forum thread 729588 (the report itself is read; the tool's "256-byte chunks, 100 ms apart" advice is its own invention and is **rejected**) |
| Bench instruments | Siglent SDM3065X US$857; Siglent SDS2104X Plus US$1,399; Keysight 34465A 10 V range ±(16 ppm of reading + 4 ppm of range), prices not found | retailer pages |
| Makers' power headers | Mutable: unshrouded 2 × 5; Intellijel: shrouded 16-pin | partly sourced; protection parts not confirmed |

## 4. Rejected answers

- **Front-panel USB mounting.** The table it returned named a maker that does not exist and gave the same sentence for every product. Nothing in it is used. C3's next-best option still rests only on Winterbloom's Sol.
- **Bare-board price.** It computed US$2.45 for five boards from a per-square-metre figure, which ignores the minimum order charge. No price is recorded.
- **DAC80508 current "per channel".** The datasheet figure is for the whole device (row 2).
- **Apple accessory power.** 4.5 W for iPhone was reported, but that sentence is not in the Apple page it cited. No figure is recorded.
- **External clock behaviour of other products.** The comparison was not traceable to the manuals it cited.
- **Short-circuit test duration in IEC 62368-1.** It cited only forum threads. No standard was read.

## 5. Still open

- Which pad the inductor's polarity dot faces. Raspberry Pi's guide confirms the dot exists and that orientation matters; the answer is in its layout figure, which no tool could read. Kiln copies the placement from Raspberry Pi's own KiCad board.
- RP2350 run current: the datasheet's section 14.9.7 exists; its table did not come through.
- The jack's height on a real part, a calliper measurement.
- Apple's numeric power limit for accessories.
- A register search for "Kiln" at EUIPO and UKIPO, and a direct USPTO search rather than a mirror.
- The price of the bare board, which needs an order form.
- How other makers mount a front-panel USB socket.

## 6. Questions no public source can answer

These need the operator, canon or a design proposal, and are in the brief or the spec:

- `BeatOvenRun.v1` and `MIDIEventStream.v1` shapes: named in canon, never defined.
- Whether an NVIDIA commitment requires an NVIDIA component.
- What CLOCK IN should do: the Output Stream contract has no message for external sync. Needs an ADR.
- Calibration commands on the Ops lane. Needs an ADR.

## 7. What the facts change

- **Kiln's power budget was understated.** With the datasheet op-amp current, normal draw is 51.7 mA on +12 V (was 40.8) and 20.5 mA on −12 V (was 11.3). Both remain inside the 120 mA and 50 mA limits. CALCULATED from OBSERVED typical figures; nothing is measured.
- **Reference buffer.** The DAC's reference could drive the 1.0 mA load directly, but would shift by 100 µV, so the buffer stays (CALCULATED).
- **Crystal drift.** 30 ppm over 60 s is 1.8 ms, not the 3 ms assumed. Temperature and ageing are extra.
- **Short-circuit test.** The op-amp's continuous rating covers one output shorted to ground. Shorts to the ±12 V rails are outside it, which is the case the test plan must prove.

## 8. Second pass, 2026-11-13

A second pass read primary sources for several items in section 5. Results and the decisions taken from them are in [../2026-11-13-delegated-decisions.md](../2026-11-13-delegated-decisions.md), sections 2 and 4. In short:

- Closed: Apple's accessory power figure (4.5 W, iPhone 15 and later; the rejection in section 4 is withdrawn), RP2350 run current, the MIDI Association's ID terms.
- Narrowed: the inductor's polarity dot (the datasheet figure implies the output side; not confirmed against Raspberry Pi's board file).
- Still open: jack height, front-panel USB mounting, bare-board price, and register searches outside the USPTO and UKIPO.
- New: the product name was decided as BeatOven, and BEATOVEN is a live US service mark held by an unrelated company.
