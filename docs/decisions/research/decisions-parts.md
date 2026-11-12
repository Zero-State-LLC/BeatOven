# Eurorack 12 HP module: three decisions (research notes, 2026-11-12)

Labels: OBSERVED = read at the cited URL this session. INFERRED = derived (basis stated). SPECULATIVE = guess.
Limits: the Thonk/QingPu PJ398SM drawings are JPEG images and could not be read as text; Firecrawl credits ran out part-way, so some items are "not found".

## Decision 1 - LEDs

### 1(a) PJ398SM dimensions
| Item | Value | Label | Source |
|---|---|---|---|
| Body width (X) | 9.0 mm (-4.5 to +4.5 mm) | OBSERVED | KiCad official footprint Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles, gitlab.com/kicad/libraries/kicad-footprints (Connector_Audio.pretty) |
| Body length (Y) | 10.45 mm (y 2.03 to 12.48 mm, pad S at y=0) | OBSERVED | same |
| Barrel centre | y = 6.48 mm from pad S, i.e. 0.78 mm toward the pad-S side of body centre | OBSERVED | same |
| Courtyard | 10.0 x 14.4 mm | OBSERVED | same |
| Keep-out under barrel | circle r=1.8 mm (3.6 mm dia) | OBSERVED | same |
| Pads | S y=0, TN y=3.1, T y=11.4 mm; drills 1.22 / 1.42 / 1.43 mm | OBSERVED | same |
| Bushing / panel hole | 6 mm bushing, 6.0-6.5 mm hole | OBSERVED | thonk.co.uk Thonkiconn page notes; sdiy.info "Eurorack panel components" (thread ~5.9 mm, 6.0-6.5 mm hole) |
| PCB to panel distance | 10.0 mm ("back of the shell to the base of the bushing ... typical PCB to panel distance"), stated for WQP-PJ301M-12 | OBSERVED (via page-query extraction) | firstpr.com.au/rwi/parts/3.5mm-sockets/ |
| Same footprint/height for PJ398SM | Thonk: PJ301M-12 and PJ398SM "functionally identical and interchangeable"; QingPu: same footprint, tab height same (1 mm) | OBSERVED | thonk.co.uk/shop/thonkiconn/ ; web.archive.org QingPu WQP-PJ398SM page |
| Body height above PCB (top of shell), thread length | not found (drawing is an image) | - | - |
| Tolerance on the 10.0 mm | not found; Thonk drawing tolerance in the old PDF is +/-0.15 mm general | INFERRED | Thonkiconn_Jack_Datasheet.pdf |
| "10-11.5 mm" claims | The 10.0 mm figure is the best-attested; treat 10.0 mm as nominal and design for +/-0.5 mm. Panel thickness (2 mm) does not change the PCB-to-panel-underside distance; panel front is then 12.0 mm above PCB. | INFERRED | - |

Derived spacing (INFERRED from the footprint above):
- Column pitch 12.70 mm: body-to-body gap = 12.70 - 9.0 = 3.70 mm; courtyard-to-courtyard gap = 2.70 mm. A 3 mm LED (flange ~3.8 mm, not verified) does not fit between columns.
- Row pitch 16.0 mm: body-to-body gap = 16.0 - 10.45 = 5.55 mm; courtyard-to-courtyard gap = 1.6 mm (courtyard includes the pin tails). Physical room for a 3 mm LED exists in the row gap; centre is about 8.8 mm from the barrel centre along Y toward the body end. Needs a custom, shrunken courtyard and checking jack nuts on the panel face (nut size not found).

### 1(b) What open designs do
| Design | Method | Label | Source |
|---|---|---|---|
| Music Thing Modular Turing Machine Mk ii | 10 red 3 mm-style flat-head LEDs pushed through panel holes, held flush with masking tape, soldered with the panel as the jig; no spacers | OBSERVED | Thonk build doc Turing_Machine_Mkii_Build_Doc_v1.01a.pdf steps 44-47 |
| Music Thing Workshop System | LEDs have flat tops flush with panel, aligned with tape or blu-tack before soldering; spacers only (from 2025) three tiny ones to protect legs | OBSERVED | musicthing.co.uk/WorkshopDocs/WorkshopBuildGuide_24-25.html |
| Mutable Instruments Rings (Sound Study Modular kit) | "slip the LED spacers on the LEDs", then fit LEDs, panel on top | OBSERVED | soundstudymodular.com Rings assembly page (a third-party kit of the Mutable design; Mutable BOM xlsx was not readable) |
| Befaco, Winterbloom, Nonlinearcircuits, Hagiwo, Gillet design notes | not found | - | - |
| Light pipes / bare SMD through translucent panel in an open Eurorack design | not found | - | - |

### 1(c) Orderable parts
LED spacers (Newark listing of Bivar, OBSERVED, newark.com/c/optoelectronics-displays/led-products/led-spacers?brand=bivar):
| MPN | Height | OD | Note |
|---|---|---|---|
| ELM 2-3MM | 3 mm | 4.8 mm | PVC, 3 mm LED; ~$0.05 at 1000+ |
| LTM-190 | 0.19 in (4.8 mm) | 0.2 in (5.1 mm) | |
| LTM-250 | 6.4 mm | 5.1 mm | |
| LTM-400 | 10.2 mm | 5.1 mm | |
| LTM-450 | 11.4 mm | 5.1 mm | |
| 456-500 | 0.5 in (12.7 mm) | 0.25 in | nylon |
TME also lists Bivar 460-160 (L 4.1 mm, fits 3 and 5 mm LEDs). Spacer sets seating height of the LED flange only; LED top = spacer height + body above flange (3 mm LED body height not verified here), so a ~5 mm spacer is the likely size for a 10 mm gap (INFERRED). A spacer OD of 4.8-5.1 mm does not fit the 3.7 mm column gap.

3 mm light pipes (Mouser, OBSERVED, mouser.com 12.7 mm LED light pipes list; prices 1-off USD):
| MPN | Type | Length | 1-off |
|---|---|---|---|
| Bivar GVLP-500-R / -F | 3 mm vertical board-mounted, 3.3 mm dia pipe | 12.7 mm | $1.03 |
| Bivar GVLP-xxx-R/-F | same series, lengths 5.1, 6.4, 7.6, 8.9, 10.2, 11.4, 12.7, 13.9, 15.2, 16.3, 16.5 mm (-200 to -650) | per MPN | OBSERVED catalog.bivar.com/viewitems/rigid-board-mount/gvlp |
| Bivar VLP-500-R | vertical SMD round face, 3 mm | 12.7 mm | $0.40 |
| Bivar PLP2-2-500 | 2 mm panel press-fit | 12.7 mm | $1.30 |
| VCC LFB050CTP | 3 mm | 12.7 mm | $0.83 |
| VCC PFL3-500 | 3 mm panel press-fit flat lens | 12.7 mm | $1.02 |
| Dialight 515-1301-0500F | flat lens | 12.7 mm | $1.02 |
Dialight 515 series countersink: minimum panel thickness 1.27 mm (so 2 mm is fine), 3 mm lens lengths 3.2/4.0/4.77/6.35/7.95/9.53/12.7/15.24 mm etc., suggested SMD LEDs 597-3XX1-207NF, 597-3XX1-607F, 598-8CX0-107F (OBSERVED, dialightsignalsandcomponents.com 515 page). Maximum panel thickness, PCB footprint/hole sizes and whether GVLP carries its own LED pad: not found.
Length estimate for a light pipe flush with a 2 mm panel front over an SMD LED about 1 mm tall: about 10 + 2 - 1 = 11 mm, so GVLP-450 (11.4 mm) or GVLP-400 (10.2 mm) are the nearest (INFERRED, unverified fit).

### 1(d) Minimum centre distance, real designs
Not found: no published panel drawing or KiCad file with LED-to-jack distance was measured. Footprint-based figures above are the only data. I found no design using 12.70 mm columns with an LED in the row gap (not found).

Cost comparison:
| Option | Extra parts | Assembly cost |
|---|---|---|
| Flat-top 3 mm THT, long legs, panel as jig | none beyond LEDs | one jig step (panel on, tape, solder LEDs with jacks); no reflow; LED legs float ~10 mm, low rework tolerance |
| 3 mm LED + spacer | 8 spacers (~$0.05-0.25 each) | spacer does not close a 10 mm gap alone; still needs panel hole alignment |
| SMD LED + light pipe | 8 light pipes ($0.40-1.30 each) + 8 SMD LEDs | reflowable, but pipe is not captured at the panel unless press-fit type; extra tolerance stack |

Recommended answer: use 3 mm flat-top THT LEDs left on long legs, soldered with the panel mounted as the alignment jig (as Music Thing Turing Machine Mk ii and Workshop System do), placed in the 5.55 mm row gap (not between 12.70 mm columns) with a shrunken courtyard; no spacers needed.
If you disagree, the next-best option: SMD LEDs under Bivar GVLP-400/-450 board-mount light pipes (verify footprint and 2 mm panel hole fit on a sample first).

## Decision 2 - USB-C through the panel

### 2(a) Candidate receptacles (target: face at or just below panel front = 12.0 mm above PCB; panel underside 10.0 mm)
| MPN | Mount | Height above PCB | Data? | Availability / price | Label |
|---|---|---|---|---|---|
| GCT USB4085 | THT, "PCB Top Mount" | 3.46 mm | 16-pin USB 2.0 | height from Mouser/powerelectronictips; 3.46 mm indicates a horizontal (right-angle) part, so NOT vertical | OBSERVED height; vertical/horizontal INFERRED |
| GCT USB4120 (16 contact USB 2.0) | vertical, SMT contacts + THT shell stakes | 6.50 mm profile | yes | LCSC USB4120-03-C (C3445864), stock 1616, USD 1.32 @1 | OBSERVED (gct.co/usb-connector/vertical; JLCPCB listing) |
| GCT USB4145 (16 contact USB 2.0, 3 stake lengths) | vertical, SMT + THT stakes | 7.46 mm | yes | USB4145-03-0170-C (C5181332) stock 2873 USD 1.41 @1; -0230-C (C5291559, 12P) stock 1799; -0070-C (C5815189) stock 2361 | OBSERVED |
| GCT USB4070 (24 contact, USB 3.2 Gen 2) | vertical SMT | 10.50 mm | D+/D- present on 24-pin (INFERRED) | LCSC USB4070-30-C (C6007487) stock 9, USD 4.21 | OBSERVED height/stock |
| GCT USB4151 (24 contact) | vertical SMT | 11.10 mm | INFERRED yes | LCSC USB4151-GF-C (C7407283) stock 24, USD 2.51, min order 4 (LCSC lists gender "Male", probably a listing error) | OBSERVED |
| GCT USB4115 (24 contact) | vertical SMT | 9.30 mm | INFERRED yes | stock not checked | OBSERVED height |
| GCT USB4130/4140/4175/4180 | vertical | 6.5 / 6.5 / 11.0 / 11.16 mm | NO, 6-contact charge only | - | OBSERVED; exclude |
| Korean Hroparts TYPE-C-31-M-17 | SMT right angle, 6P | 6.8 mm length | NO (6P, 3,000 cycles) | C283540, stock 9875 | OBSERVED; it is right-angle, not vertical |
| Korean Hroparts TYPE-C-31-M-06 / -07 | vertical SMT 24P | "length 8.5 mm" | protocol blank | -06 stock 974, USD 0.85; -07 stock 13 | OBSERVED; height meaning not verified |
Not found: Molex, JAE, Kycon, Amphenol 12401548E4#2A, Wurth 632722 vertical data variants; DigiKey prices.

Fit (INFERRED from 10.0 mm gap): USB4145 face sits 2.5 mm behind panel underside = 4.5 mm below the panel front; USB4120 5.5 mm below; USB4070 (10.50 mm) 1.5 mm below front (0.5 mm above panel underside... face at 10.5 mm, front at 12.0 mm); USB4151 (11.10 mm) 0.9 mm below front. Plug shell insertion depth: not verified here, so a 4.5 mm recess may let the overmold touch the panel. Tolerance on the 10.0 mm gap also matters.

### 2(b) Existing modules
| Module | USB | Label |
|---|---|---|
| Expert Sleepers ES-9 | Type C, 16 HP, 14 in + 11 out; socket location not stated | OBSERVED expert-sleepers.co.uk/es9.html |
| Expert Sleepers ES-8 | Type B, 8 HP, 12 jacks; location not stated | OBSERVED es8.html |
| Expert Sleepers FH-2 | USB host Type A and device Type C, 8 HP; location not stated | OBSERVED fh2.html |
| Befaco MIDI Thing V2 | has a USB host; 6 HP, 30 mm deep, 12 assignable ports; connector type/mounting not stated | OBSERVED befaco.org/midi-thing-v2/ and manual |
| Intellijel, Noise Engineering, Winterbloom, ALM, Bastl, crow/teletype | not found | - |
No source found describing how any of these mount the connector (vertical, daughterboard, pigtail).

### 2(c) Alternatives
- Slot-in daughterboard: a KiCad forum thread describes a USB-C breakout PCB inserted into a 1 mm slot in the main board to sit vertical at 11 mm from a front panel, with pad/slot advice (OBSERVED, forum.kicad.info thread 26396). This is a proven approach for exactly this geometry.
- Panel-mount USB-C pigtail/extension, or rear/top-edge port: not researched (not found).

Recommended answer: use GCT USB4145-03-0170-C (vertical, 16-contact USB 2.0, 7.46 mm, LCSC C5181332, USD 1.41, stock 2873) and plan a 2.5 mm recess, verifying plug depth on a mock-up; if the recess is too deep, fix it with the slot-in daughterboard to raise the face.
If you disagree, the next-best option: GCT USB4070-30-C (10.50 mm, face 1.5 mm below panel front) at about USD 4.21 but only 9 in stock.

## Decision 3 - 12 HP and jack pitch

| Module | HP | Jacks | Label | Source |
|---|---|---|---|---|
| Expert Sleepers ES-8 | 8 | 12 x 3.5 mm | OBSERVED | expert-sleepers.co.uk/es8.html |
| Expert Sleepers FH-2 | 8 | about 10 (8 CV out + 2 CV in, not confirmed complete) | OBSERVED | fh2.html |
| Expert Sleepers ES-9 | 16 | 25 (14 in, 11 out incl. 1/4 in) | OBSERVED | es9.html |
| Befaco MIDI Thing V2 | 6 | 12 ports | OBSERVED | befaco.org |
| Your module | 12 | 16 | - | - |
North Coast Synthesis regression: about 1 HP wider per extra jack on average; 2 HP (10.16 mm) spacing called safe for a row so you can grab plug bodies (OBSERVED, northcoastsynthesis.com/news/reality-check-hp/). Your density is 0.75 HP per jack, denser than average but the ES-8 (0.67 HP per jack) shows 8 HP is shippable. ModularGrid HP numbers and manufacturer panel drawings: not found (not accessed). The "12-14 mm comfortable pitch" claim: not found as primary source; 12.70 mm is above the 10.16 mm North Coast minimum (INFERRED).
Moving to 13.5 mm column pitch: 4 columns span 40.5 mm on a 60.6 mm panel, leaving 10.05 mm margins, so it fits (INFERRED arithmetic). Gain: body gap 3.70 -> 4.50 mm, still too small for a 3 mm LED with annulus; it does not solve the LED problem, the row gap does. No published evidence that 13.5 mm is standard (not found).

Recommended answer: stay at 12 HP with 12.70 mm column pitch (16 jacks, ES-8 shows 8 HP with 12 jacks is accepted; 12.7 mm pitch exceeds the 10.16 mm grab minimum) and put LEDs in the 5.55 mm row gap rather than widening columns.
If you disagree, the next-best option: 13.5 mm column pitch for patching comfort (fits in 60.6 mm), keeping LEDs in the row gap.

## Could not verify
- PJ398SM body height above PCB, thread length and tolerance on the 10.0 mm gap (drawings are images; only the firstpr 10.0 mm statement for PJ301M-12 found).
- Jack nut outer size, so panel-face clearance for LEDs is unchecked.
- Any design with a measured LED-to-jack centre distance; any use of 12.70 mm columns with LEDs in the row gap.
- Befaco, Winterbloom, Nonlinearcircuits, Hagiwo, Gillet LED practice; Mutable BOM LED spacer part number.
- GVLP footprint, max panel thickness for light pipes, 3 mm LED body height.
- USB connector placement/mounting of ES-8/ES-9/FH-2/MIDI Thing; Intellijel, NE, Winterbloom, ALM, Bastl, crow, teletype USB; Molex/JAE/Kycon/Amphenol/Wurth vertical USB-C; DigiKey prices; plug insertion depth.
- ModularGrid HP numbers and manufacturer panel drawings for jack pitch.
