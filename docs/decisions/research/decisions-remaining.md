# Decisions remaining: verification of previously UNVERIFIED items

Date of research: 2026-11-12. All web access through context.dev only (search + scrape).
Labels: OBSERVED = read through context.dev at the cited URL this session; INFERRED = basis stated; SPECULATIVE = guess.

## 1. Thonkiconn PJ398SM / WQP518MA height, thread, PCB-top-to-panel-underside

| Source | Statement | Label |
|---|---|---|
| exploding-shed.com/thonkiconn-mono-wqp518ma-1-pc/100515P001 (retailer) | "effective total body height 10mm, threading 4,5 mm"; 6 mm panel hole | OBSERVED |
| firstpr.com.au/rwi/parts/3.5mm-sockets/ (builder measuring the predecessor WQP-PJ301M-12, same footprint) | "back of the shell to the base of the bushing is 10.0mm", called the typical PCB-to-panel distance | OBSERVED |
| land-boards.com/blwiki/index.php?title=Eurorack_Panel_Jacks | list says "PJ-398SM Mono Jack = 9mm" height from board; the same page says other panel parts are 10 mm and PJ398SM is the right match | OBSERVED (internally inconsistent: 9 mm vs about 10 mm) |
| qingpu-electronics.com/en/products/wqp-pj398sm-362.html (maker) | footprint same as WQP-PJ301M-12; mounting tab "still 1mm" tall; no body-height or thread number on the page | OBSERVED |
| thonk.co.uk/shop/thonkiconn/ | says WQP518MA = PJ398SM = PJ301M-12 footprint and tab height; the Thonk datasheet PDF itself returned an access error (WEBSITE_ACCESS_ERROR) | OBSERVED |

- Thread length 4.5 mm (one retailer; a ModWiggler poster calls PJ301-type threads "5mm", forum remark only).
- Design number: PCB top to panel underside about 10 mm (range 9 to 10 mm across sources). With a 2 mm panel, the thread (4.5 mm) leaves 2.5 mm for nut and washer: INFERRED (4.5 minus 2).
- Not found: the Thonk/QingPu dimensioned drawing (PDF not reachable); tolerance on the 10 mm.

Bottom line: PCB-top-to-panel-underside is about 10 mm for PJ398SM/WQP518MA (two independent sources at 10 mm, one list at 9 mm), thread 4.5 mm from a single retailer; confirm against the QingPu/Thonk drawing before fixing standoffs.

## 2. Front-panel USB socket with the PCB parallel to the panel

| Product | Finding | Label |
|---|---|---|
| Winterbloom Sol rev1 (open hardware, CC-BY-SA 4.0) | Repo folders `hardware/rev1/jackboard`, `mainboard`, `panel`. `jackboard.sch` has J11 USB_B with footprint `Connector_USB:USB_B_TE_5787834_Vertical`. So the USB socket is a vertical receptacle on a separate front "jackboard", not on the mainboard. (raw.githubusercontent.com/wntrblm/Sol/master/hardware/rev1/jackboard/jackboard.sch) | OBSERVED |
| Befaco MIDI Thing V2 | Quick-start guide: "Connect expansion panel micro-usb cable to Teensy USB port on the back of the PCB." USB device goes via a cable to an expansion panel (befaco.org/docs/Midi_thing_V2/Midi_Thing_V2_Quick_start_guide_A4.pdf) | OBSERVED |
| Snazzy FX ARDCORE | ModWiggler poster says it "Seems to have a usb socket mounted on a pcb that is parallel" to the panel (hearsay, t=165852) | OBSERVED (forum remark) |
| ModWiggler t=165852 advice | GCT through-hole micro-USB for parallel boards; a TE USB-B vertical; a few mm of socket proud of the panel for support | OBSERVED (forum remark) |
| CopycatMusic ComposerMIDICV (hobby RP2354A, 4 HP, USB-C plus TRS MIDI) | README lists USB-C; connector part and mounting not stated on the main page | OBSERVED (comparable only) |
| monome crow, Expert Sleepers ES-9 / FH-2, Noise Engineering, ALM, Intellijel | Mounting method and connector part not found in any source read (crow repo has no hardware folder; ES manuals only say "USB C socket") | not found |

- Pattern across the evidence: vertical receptacle on a front daughter or jack board (Sol), or cable to a panel (Befaco). A right-angle part on the main PCB is not evidenced.

Bottom line: the only open-hardware proof is Winterbloom Sol (vertical USB-B on a separate front jackboard, TE 5787834 footprint); for the others the method is not found, so a vertical panel-side receptacle on the jack-height PCB is plausible but not shown by a shipping BOM.

## 3. GCT USB4145

| Item | Value | Label |
|---|---|---|
| Product page gct.co/connector/usb4145 | USB 2.0, Type C, 16 contacts, vertical, top entry, SMT with through-hole shell stakes, profile 7.46 mm, shell stake lengths 0.70 / 1.70 / 2.30 mm, 20,000 mating cycles, footprint-compatible with 24-pin USB4160 | OBSERVED |
| Ordering grid, datasheet drawing (mouser.com/catalog/specsheets/Global_Connector_Technology_usb4145.pdf, rev A2, 28 June 2022) | Variants USB4145-03-0070-C, -0170-C, -0230-C ("C = Tape & Reel with Cap", 03 = 3 u" gold). Title "USB2.0 Type C Receptacle, Vertical, SMT, H=7.46mm, 16 Pin" | OBSERVED |
| Pin table in the same drawing | A6 Dp1, A7 Dn1, B6 Dp2, B7 Dn2 (D+/D- present); A5/B5 CC; A4/A9/B4/B9 VBUS; SBU pins listed | OBSERVED |
| Mating view (sheet 3/4) | Text lists "Panel for plug", "6.55 min." and "4.60 max."; the extraction does not tie the numbers to dimension lines | OBSERVED (text only); meaning of 4.60 max SPECULATIVE: view the PDF sheet visually |
| USB-IF Type-C Locking Connector spec Annex A (usb.org, rev 1.0, informative) | "minimum plug shell length is 6.55 mm"; distance from receptacle mating datum to the surface the plug overmold seats against should be "a maximum of 6.5 mm" | OBSERVED |
| USB Type-C spec R2.0 (cited via github.com/dudgeon/count-fidget/issues/4; Amphenol page) | Plug overmold up to 12.35 mm wide x 6.5 mm high; receptacle Datum A is 6.20 mm behind the mouth (reference) | OBSERVED (secondary citation of R2.0; Amphenol quotes the same 12.35 x 6.5 mm) |

Design consequence for this module (INFERRED from numbers above):
- Mouth height above PCB 7.46 mm; panel underside about 10 mm above PCB (item 1); 2 mm panel gives outer face about 12 mm. Mouth recess behind the outer face = 12 - 7.46 = about 4.5 mm.
- USB-IF guidance (seat surface at most 6.5 mm from datum, so at most about 0.3 mm proud of the mouth) cannot be met by a panel face 4.5 mm in front of the mouth. The panel cutout must therefore pass the whole overmold (up to 12.35 x 6.5 mm plus clearance), or the receptacle must sit near flush (a taller connector, a raised board, or a daughterboard).
- No maker documentation of a "maximum panel thickness" for USB-C was found.

Bottom line: USB4145 is a 16-contact USB 2.0 vertical receptacle, 7.46 mm tall, variants -0070/-0170/-0230, with D+/D- on A6/A7/B6/B7; at a roughly 10 mm board-to-panel gap its mouth sits about 4.5 mm behind a 2 mm panel's outer face, so a large overmold-sized cutout or a flush-mount arrangement is required.

## 4. Eurorack power header practice and reverse protection

| Maker | Finding | Label |
|---|---|---|
| Winterbloom Sol (open) | `mainboard.sch` J1 `SF Connectors:2X5-SHROUDED`, MPN 61201021621, note "Eurorack Power"; two 1N4148W SOD-123 diodes (D1, D2) in the power section; topology not traced | OBSERVED (shrouded 10-pin); diode role INFERRED |
| Mutable Instruments | diysynthmnl.github.io/p/powering-your-module: power input of a Mutable module = "IDC input, Reverse polarity protection, Filter caps" (circuit shown as image; header shroud and part numbers not readable). Schematic files are Eagle XML and did not scrape | OBSERVED (text); shroud/part not found |
| Befaco MIDI Thing V2 | Schematic text (MIDI_THING_2_schematic.pdf) lists two SS14 Schottky parts near V+/V- (placement not verified); the user manual still warns "you might burn it out" if plugged in backwards; header size/shroud not found | OBSERVED; protection effectiveness not established |
| Noise Engineering | Blog: modules "have some protection built in" but not all modules do; notes keyed headers help but can force a wrongly made cable | OBSERVED |
| ALM Busy Circuits | Pamela's NEW Workout manual: "Skiff friendly / Reverse power protection"; O/A/x2 retailer page: "Supply: +/-12V (Reverse voltage protection)", depth including power header | OBSERVED; header type not found |
| Intellijel | Only a ModWiggler user report that the VCO-2RM has reverse polarity protection; manuals read mention no header practice | forum remark only; not found |
| Make Noise | not found (only Reddit hearsay that reverse polarity is "pretty common") | not found |
| Community norm | ModWiggler t=266645 "use shrouded power headers"; t=113628: common options are series Schottky diodes or reverse diode plus fuse; Perfect Circuit: reverse protection "is common" but not universal | OBSERVED (forum/retailer) |

Bottom line: shrouded 2x5 headers (Sol) plus series diode or Schottky protection (Mutable, Befaco, ALM, Noise Engineering all claim some protection) is the evidenced practice; 10 versus 16 pin per maker and the protection parts for Intellijel and Make Noise are not found.

## 5. 1 V/oct reference note and pitch range

| Product | Note at 0 V | Pitch CV range | Source (label) |
|---|---|---|---|
| Expert Sleepers FH-2 | MIDI note 60 (C4) is the "centre" CV, 0 V when range is +-5 V; note 96 = centre +3 V | per-output selectable 0-10 V, +-5 V, 0-1.8 V, 0-5 V, 0-8 V | fh2_user_manual_1.24.pdf (OBSERVED) |
| Mutable Yarns | MIDI note 36 | not found (gates +5 V) | Yarns quickstart PDF: "CVs are 1 V/Oct, 0V = MIDI note 36" (OBSERVED) |
| Doepfer A-190-4 | reference note default C2 = MIDI note 24 (adjustable 12-72); TUNE offset "normally set to 0V" so the reference note sits at 0 V | CV1 -3 V to +10 V; CV2 0 V to +10 V; 1.00 V/oct, 12-bit DAC | A190_4_man.pdf (OBSERVED; "reference note = 0 V" INFERRED from TUNE text) |
| Arturia KeyStep | user-selectable "0 Volt MIDI Note" for V/oct (value list not read); Hz/V uses 1 V note | pitch CV range not found; Mod CV max 5 to 12 V | KeyStep manual pages (OBSERVED) |
| Arturia BeatStep Pro | "0 Volt MIDI note range: 0-127" (selectable, INFERRED) | 1 V/oct "(0-10V)"; V-trig gate 10-12 V | BeatStep Pro manual 2.0 (OBSERVED) |
| Korg SQ-1 | not found | CV range setting 1 V, 2 V, 5 V (V/oct) or 8 V (Hz/V); gate 10 V | korg.com SQ-1 specifications (OBSERVED) |
| Intellijel uMIDI | MIDI note 0 (C-2) = 0 V, note 120 (C8) = 10 V | 0 to 10 V | umidi_manual_2018.09.13.pdf (OBSERVED) |

- Note numbering conventions differ (C-2 vs C0 names for MIDI note 0): compare by MIDI note number only.

Bottom line: there is no single 0 V note (Yarns 36, Doepfer 24, uMIDI 0, FH-2 60 at the centre of a +-5 V range, Arturia selectable), so make the 0 V note and range user-configurable and document them in MIDI note numbers.

## 6. Raspberry Pi USB PID allocation (VID 0x2E8A) and pid.codes

Raspberry Pi (github.com/raspberrypi/usb-pid README; Raspberry Pi docs microcontroller-chips.adoc):
- OBSERVED: USB-IF let Raspberry Pi "sub-license" PIDs under VID 0x2E8A for devices using the RP2040/RP2350 silicon in a customer product; each allocation is agreed with USB-IF.
- OBSERVED: a unique PID is only needed for a custom Windows driver or to be uniquely identifiable; otherwise use standard class drivers and distinguish by iManufacturer / iProduct / iSerial strings.
- OBSERVED: the README table has a "Commercial" section (0x1000-0x1fff) of company products (Cytron, Pimoroni, Adafruit, etc.), so commercial products do get PIDs.
- Process (OBSERVED, Google form linked from README): fields are email, legal company name, company address, contact, product name, purpose, description, product link, estimated annual usage of RP2040 devices, estimated production start; optionally reserve before launch and add the product by pull request to the README table when public (else the allocation is lost).
- Cost: not found (neither README nor form states a fee; absence of a statement is not proof it is free). Conditions beyond the above: not found.

pid.codes (pid.codes/howto, /faq):
- OBSERVED: only for projects with a public repository, modifiable PCB design files and/or source, under a recognised open-source or open-source-hardware license; both hardware and software must be open if both exist.
- OBSERVED: pull-request process on VID 1209; PIDs 0xxx and 1xxx reserved; FAQ: no income from users ("accept no income"), i.e. free. FAQ also says it is not supported or endorsed by USB-IF.
- INFERRED: a closed-source commercial module would not qualify at pid.codes but can apply to Raspberry Pi.

Bottom line: a commercial RP2350 product can request a PID through the Raspberry Pi form (company details, annual volume, start date; fee not stated), while pid.codes is free but open-source/open-hardware only; a class-compliant USB-MIDI device does not strictly need either if string descriptors suffice.

## 7. iOS/iPadOS, class-compliant USB-MIDI, power, SysEx

| Topic | Finding | Label |
|---|---|---|
| Supported device class | Apple support 111811: Apple USB-A camera adapters work with "Audio/MIDI interfaces and devices" | OBSERVED |
| Power errors | Same page: devices needing more power may trigger "attached accessory uses too much power"; remedies: powered USB-A hub or the Lightning to USB 3 Camera Adapter with its own power input | OBSERVED |
| Numeric limit | Apple states no number on that page. A 2013 Pocketables article says Apple cut adapter output from 100 mA to 20 mA (30-pin/Lightning era). doc.crudebyte.com says the iPad delivers "very limited" power | secondary reports only; current USB-C limits not found |
| SysEx API | Core MIDI MIDISendSysex: "Asynchronously sends a single system-exclusive (SysEx) event", iOS 4.2+ / iPadOS 4.2+ (developer.apple.com) | OBSERVED |
| SysEx problems | Apple Developer Forums thread 729588 (May 2023, one developer): on iOS, after sending SysEx "all midi messages after that for the next 500ms are simply dropped" (his report, unconfirmed by Apple); MIDI 2.0 UMP SysEx send "doesn't do anything at all" | OBSERVED (single developer report) |

- INFERRED design rule: make the module self-powered from the rack (not bus-powered) and keep USB descriptor bMaxPower small; keep SysEx messages short, send them one at a time and pace other traffic after them.

Bottom line: iOS accepts class-compliant USB-MIDI devices via Apple's camera adapters but Apple gives no current figure, so a rack-powered device drawing minimal or no bus current avoids the "uses too much power" alert; SysEx works through Core MIDI but one developer reports 500 ms of dropped traffic after a SysEx send on iOS.

## 8. Fail-safe behaviour of comparable products

| Product | Documented behaviour | Label |
|---|---|---|
| Doepfer A-190-4 | CC 123 All Notes Off: "the gate is turned off, and all notes ... are cleared. Control voltages remain at the level at which they were set at last." CC 121 resets LFO and glide. No USB-disconnect or active-sensing behaviour stated | OBSERVED (A190_4_man.pdf) |
| Expert Sleepers FH-2 | CC 120 and CC 123 are used as All Notes Off by the MIDI/CV converters unless mapped elsewhere; nothing on host loss | OBSERVED (fh2_user_manual_1.24.pdf) |
| Befaco MIDI Thing V2 | Global-menu "PANIC!: Sends All Note-OFF in all channels"; loads last saved state at startup; nothing on host loss | OBSERVED |
| Polyend Poly 2 | "Panic!" menu function releases voices; user reports of stuck gates at power-up (ModWiggler t=221437) | OBSERVED (manual); forum report |
| Mutable Yarns | not found (no manual text on panic or host loss; MIDIpal archive has a `notenuke` app, a different product) | not found |
| MIDI active sensing | Spec mirror: device sends 0xFE "at least once" every 300 ms of silence; receivers expecting it can treat loss as broken connection | OBSERVED (midi.teragonaudio.com/tech/midispec/sense.htm; the 300 ms rule applies to 5-pin DIN, not USB) |

- None of the comparables documents an automatic timeout; all rely on a host-sent All Notes Off or a manual panic. Hold-CV-and-drop-gate (Doepfer) is the only stated CV policy.
- SPECULATIVE: USB loses the link electrically (suspend/disconnect events), so a device can detect host loss without active sensing.

Bottom line: comparable products only drop gates (and hold CV) on a received All Notes Off or a manual panic, with no documented automatic timeout; the A-190-4 model (gates off, CV held) is the one documented policy.

## 9. Name "Kiln" (findability report, not legal advice)

| Question | Finding | Label |
|---|---|---|
| Vitric Audio "Kiln" | Exists: "Kiln Synthesizer", wavetable synth plugin with Glass modal resonator and Anneal patch search, VST3 / AU / AAX, macOS and Windows, v1.1.3 (kvraudio.com/product/kiln-synthesizer-by-vitric-audio; vitricaudio.com/kiln) | OBSERVED |
| Release date | Rekkerd article dated 2 Sep 2026 reports Vitric launching its lineup including Kiln Synthesizer; KVR shows $100 list, $49 sale to 20 Nov 2026. Exact Kiln 1.0 date not found | OBSERVED; release about Sep 2026 INFERRED |
| Publisher | Vitric press page: American plugin developer, a Delaware LLC based in Canton, Ohio; Studio 4 in Cleveland per Rekkerd | OBSERVED |
| Eurorack module, pedal or hardware named Kiln | None found: search engine results, Sweetwater site search (no matches), Reverb query (no matches). ModularGrid search page returned no readable results (inconclusive) | not found (absence not proven) |
| Trademark record | USPTO tmsearch.uspto.gov scraped only a script shell with no results; no record reachable. No (TM) or (R) symbol next to "Kiln" on vitricaudio.com text | not reachable |

Bottom line: a software synth called Kiln by Vitric Audio (launched around Sep 2026, priced $49 to $100) already occupies the name in music technology, no Kiln hardware was found, and trademark status could not be checked (USPTO not scrapable), so run a manual USPTO/EUIPO search before committing.

## 10. TRS MIDI Type A

- OBSERVED (midi.org, "Specification for Use of TRS Connectors with MIDI Devices" and TRS adapter news): the specification exists and defines TRS wiring, but the document is download-for-members only; the public pages carry no pin table.
- OBSERVED (midi.org community thread, member post): the MIDI Association spec "uses the pin assignment that is called Type A".
- OBSERVED (minimidi.world, community guide, says Type A became the MIDI standard in 2018):

| TRS | DIN pin | Role |
|---|---|---|
| Tip | 5 | current sink (data) |
| Ring | 4 | current source (+5 V via resistor) |
| Sleeve | 2 | shield |

- Sleeve at a MIDI IN: the public MIDI pages do not state it. OBSERVED (search highlight, eventools.io DIN-5 page): shield on pin 2 is "only the sending device grounds". INFERRED: a MIDI IN leaves the sleeve unconnected (receiver ground stays isolated by the optocoupler).
- Type B (Arturia, Novation, 1010music) swaps tip and ring (OBSERVED, minimidi.world), so a Type A input that auto-detects (as some 1010music and LPZW modules do) is safer.

Bottom line: Type A is tip = DIN 5 (sink), ring = DIN 4 (source), sleeve = DIN 2 (shield), confirmed by a community guide and a member post but not by an openly readable MIDI Association page; do not tie sleeve to ground on the input.

## 11. Trigger and clock conventions

Doepfer A-100 technical details (doepfer.de/a100_man/a100t_e.htm), OBSERVED:
- Trigger/gate/clock signals are rectangles with "typical voltage levels of 0/+5 V"; "usually any voltage beyond about +3V is treated as 'high'"; all A-100 modules withstand up to +12 V; rising edge triggers.
- Trigger length: not found (no minimum or typical pulse length stated on the page or in the A-190-4 manual).

Clock rates:

| Source | Statement | Label |
|---|---|---|
| Doepfer A-190-4 | MIDI clock is "1/96th notes" (96 per whole note = 24 PPQN); output divisor 1 to 61 | OBSERVED |
| ALM Pamela's NEW Workout manual | syncs to external clock "at 48 to 1 PPQN"; default is DIN-Sync-like 24 PPQN | OBSERVED |
| Arturia BeatStep Pro manual | clock in/out can use 24 ppqn, 48 ppqn, 2 ppqn "or even a single pulse per step" | OBSERVED |
| Korg SQ-1 | sync in/out is per step ("SYNC x1" / "x2" steps per clock, third-party summary studiocode.dev); a PPQN figure not found | OBSERVED (secondary) |

Bottom line: use 0 V / +5 V gates with the high threshold about +3 V and tolerate up to +12 V; pulse length is not specified by Doepfer, and clock outputs should offer at least 1, 2, 4, 24 (and 48) PPQN, with 24 PPQN as the default.

## 12. Pitch discrimination (just-noticeable difference)

- Source: M. N. Kunchur, "The human auditory system and audio", Applied Acoustics 211 (2023) 109507 (arxiv.org/pdf/2307.00084v2), Table 1 of frequency JNDs in cents (citing earlier measurements), OBSERVED.
- Quote: "Frequency discrimination is keenest around 2000 Hz ... JND = 3 cents."

| Frequency | Level | JND (cents) | Label |
|---|---|---|---|
| 2000 Hz | 30 dB SPL and above | 3 | OBSERVED |
| 1000 Hz | 30 to 60 dB SPL | 6 | OBSERVED; column alignment INFERRED |
| 250 Hz | 30 to 80 dB SPL | 17 to 19 | OBSERVED; column alignment INFERRED |
| 125 Hz | 30 to 60 dB SPL | 43 to 48 | OBSERVED; column alignment INFERRED |
| 31 Hz and 62 Hz | listed levels | 60 to 220 | OBSERVED |

- Also OBSERVED: trained musicians can do under 2 cents; the same paper says complex tones and two-ear listening can reach about 1 cent. The SonicBench arXiv abstract gives 10 to 20 cents for typical adults (secondary).
- Conversion INFERRED: 1 cent = 0.0833 mV at 1 V/oct (1 V / 1200), so 3 cents = 0.25 mV and 10 cents = 0.83 mV.

Bottom line: the pitch JND is about 3 to 6 cents for mid-range pure tones (Kunchur 2023, Table 1) and rises to 17 cents or more below 250 Hz, so 1 cent (about 0.083 mV) is a safe CV resolution target and 10 cents is the audible limit for most listeners.

## 13. JLCPCB capabilities (jlcpcb.com/capabilities/pcb-capabilities, fetched 2026-11-12)

| Parameter (multilayer, 1 oz outer) | Value | Label |
|---|---|---|
| Min track / space | 0.09 / 0.09 mm (3.5 / 3.5 mil); 1-2 layer 0.10 / 0.10 mm; 2 oz multilayer 0.15 / 0.15 mm | OBSERVED |
| Min via hole / diameter | 0.15 / 0.25 mm (0.1 / 0.2 mm only for boards of 1 mm or less with ENIG/OSP); preferred min hole 0.2 mm; diameter at least hole + 0.1 mm (0.15 mm preferred); smaller sizes cost more | OBSERVED |
| PTH annular ring | at least 0.20 mm; multilayer 1 oz: recommended 0.20 mm, absolute minimum 0.15 mm | OBSERVED |
| PTH to track | 0.28 mm minimum (0.35 mm recommended); via hole to track 0.2 mm; NPTH to track 0.2 mm; pad to track 0.1 mm | OBSERVED |
| Hole spacing | via hole to hole 0.2 mm; pad hole to hole 0.45 mm | OBSERVED |
| Board thickness | includes 1.6 mm (+-10 %); 4-layer max size 663 x 593 mm | OBSERVED |
| Price, 5 pcs of about 60 x 108 mm, 4-layer | not found: jlcpcb.com and cart.jlcpcb.com/quote render the calculator client-side (shows $0.00); homepage only shows "From $2.00 / 5 pcs" for the entry 2-layer service | not found |

Bottom line: standard 4-layer capability is 0.09 / 0.09 mm track/space, 0.15 / 0.25 mm via, 0.20 mm annular ring (0.15 mm absolute), PTH-to-track 0.28 mm minimum; a quote for 5 pieces of 60 x 108 mm needs the interactive calculator (not found).

## 14. TI DAC80508 (ti.com/lit/ds/symlink/dac80508.pdf; document SLASEL1D, June 2017 revised August 2018)

| Item | Datasheet content | Label |
|---|---|---|
| Output settling time | Section 7.5 Electrical Characteristics, "DYNAMIC PERFORMANCE": "Output voltage settling time", 1/4 to 3/4 scale and 3/4 to 1/4 scale, to +-2 LSB, VDD = 5.5 V, VREFIN = 2.5 V, Gain = 2: 5 us; slew rate 1.8 V/us; power-up time 12 us | OBSERVED (min/typ/max column not distinguishable in extraction; treat as typical) |
| Load conditions | Max capacitive load 2 nF (no resistive load) or 10 nF with RLOAD = 2 kohm; DC output impedance 0.085 ohm at midscale | OBSERVED |
| Error band in volts | +-2 LSB of 16 bits at 5 V full scale is about 0.15 mV | INFERRED |
| Update spacing | "a minimum wait time of 1 us is required between DAC output updates" (section 8.3 DAC update) | OBSERVED |
| REF capacitor | Section 8.3.2 internal reference: "A minimum 150 nF capacitor is recommended between the reference output and GND for noise filtering." Reference noise density quoted with REFLOAD = 10 nF. VDD bypass 0.1 to 0.22 uF X7R or NP0 (layout section) | OBSERVED |
| Power-on reset | Section 8.3.3.1: POR sets registers to defaults; outputs held at zero scale or midscale "until a valid code is written". Device Comparison Table: Z grade (DAC80508Z, ZC) resets to zero scale; M grade (DAC80508M, MC) resets to midscale. DAC data register reset 0x0000 (Z) or 0x8000 (M). ZC/MC variants add a CLR pin; Z/M use SDO | OBSERVED |
| Sync update registers | 8.6.3 SYNC register, address 0x2, reset 0xFF00: bits DACn-SYNC-EN (bits 7:0), 1 = update on LDAC trigger, 0 = update on CS rising edge (reset 0 = asynchronous); bits 15:8 DACn-BRDCAST-EN. 8.6.6 TRIGGER register, address 0x05, reset 0x0000: bit 4 LDAC ("synchronously load those DACs that have been set in synchronous mode in the SYNC register"); bits 3:0 SOFT-RESET (write 1010 to reset). Related: CONFIG register 0x3, GAIN register 0x04 | OBSERVED |

- Table captions: "Table 14. TRIGGER Register Field Descriptions"; functional block diagram labels "LDAC Trigger (synchronous mode)".
- A newer datasheet revision than SLASEL1D may exist; this is the revision served at the symlink on the fetch date.

Bottom line: DAC80508 settles in 5 us to +-2 LSB (1/4 to 3/4 scale, VDD 5.5 V, 2.5 V reference, gain 2), wants at least 150 nF on REF, powers up at zero scale (Z) or midscale (M), and synchronous update is SYNC register 0x2 (DACn-SYNC-EN) plus TRIGGER register 0x05 bit 4 (LDAC).

## Still not found
- Thonk/QingPu dimensioned drawing for PJ398SM/WQP518MA; reconcile 9 mm vs 10 mm height.
- Mounting method and connector part for USB on Expert Sleepers ES-9/FH-2, monome crow, Noise Engineering, ALM, Intellijel (only Sol and Befaco evidence found).
- Mutable, Befaco, Intellijel, Make Noise power header sizes and exact protection parts (Mutable schematics are Eagle XML and could not be scraped).
- Yarns pitch CV range; KeyStep pitch CV range and 0 V note list; Korg SQ-1 0 V note.
- GCT drawing sheet 3/4 meaning of "4.60 max" (needs a visual read of the PDF); any maker-documented maximum panel thickness for USB-C.
- Raspberry Pi PID fee and any extra conditions; Doepfer trigger pulse length.
- Apple numeric current limit for current iPhone/iPad ports; Apple-documented SysEx limits on iOS.
- Automatic host-loss timeout behaviour of FH-2, Yarns, Poly 2, Befaco.
- Any Kiln hardware (absence not proven) and any USPTO record; exact Kiln 1.0 release date.
- JLCPCB price for 5 pieces of 60 x 108 mm 4-layer.
- MIDI Association's own readable Type A pin table (specification is members-only).

## Credits used
credits_used: 241 (value returned by GET https://api.context.dev/v1/org/usage at the end of this session; it may include the earlier 16-search batch)
