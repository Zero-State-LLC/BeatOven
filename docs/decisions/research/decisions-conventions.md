# Decisions and conventions: Eurorack USB-MIDI CV/gate module (RP2350)

Research date: 2026-11-12. Labels: OBSERVED = read at the cited URL this session (page text, or an extraction query run on that URL); INFERRED = basis stated; SPECULATIVE = judgement. "not found" = I looked and did not find it. Not legal advice.

Caveat on method: several "OBSERVED" items were read through the scraper's query/extraction mode, not a raw page dump. Quoted numbers should be re-checked against the cited URL before they go in a spec.

---

## 1. Autorouter: Freerouting for a KiCad 10 board

| Question | Finding | Label |
|---|---|---|
| Home / maintainer | github.com/freerouting/freerouting; releases signed by user `andrasfuchs` (András Fuchs); README says original Java program from 2004 by Alfons Wirtz (the second via KiCad forum post by John_Pateman) | OBSERVED (github.com/freerouting/freerouting, /releases; forum.kicad.info thread 30441) |
| Licence | GPL-3.0 | OBSERVED (repo sidebar) |
| Latest release | v2.5.0, 2026-10-05 (releases page shows it as "Latest") | OBSERVED (github.com/freerouting/freerouting/releases) |
| Distribution | GitHub Releases. Assets: linux-x64 zip, macos-arm64 dmg, macos-x64 dmg, windows msi, AppImage, plain `freerouting-2.5.0.jar`, `freerouting-cli-2.5.0-checksums.txt`. GitHub lists a SHA-256 per asset (jar: f6f51bb0...e3c7, macos-arm64.dmg: a436117d...ba13d). The release tag commit carries GitHub's "verified" GPG signature (key B5690EEEBB952194). No separate detached signature on the jar seen; installers' code-signing/notarisation status not found | OBSERVED (releases page); notarisation: not found |
| Java required | Release notes of an earlier release say the project "now requires and builds with Java 25". v2.5.0 adds native GraalVM CLI executables (Linux x64, macOS arm64, macOS x64, Windows x64) that "eliminate the Java JRE requirement for CLI users" | OBSERVED (releases page) |
| JRE source | README: install a JRE from adoptium.net/temurin/releases. Adoptium lists Temurin jdk-25.0.5+8 dated 2026-10-22. Homebrew cask `temurin` currently resolves to JDK 27 (aarch64 pkg `OpenJDK27U ... 27.0.1.0.2`), NOT 25. Versioned casks exist as `temurin@17` / `temurin@21`; `temurin@25` is the natural pattern but I did not see it listed | OBSERVED (README, adoptium.net page, formulae.brew.sh/cask/temurin); `temurin@25` = INFERRED |
| Headless CLI | `java -jar freerouting.jar -de Board.dsn -do Board.ses` ; `--gui.enabled=false` disables GUI; `-inc GND,VCC` skips listed net classes; `--router.autorouter.max_passes=N`; `--router.optimizer.enabled=false`; `-drc file.json` writes a KiCad-schema DRC report; `--user_data_path=DIR`; `-da` disables anonymous analytics | OBSERVED (docs/command_line_arguments.md on raw.githubusercontent.com) |
| KiCad 10 integration | v2.5.0 adds a "KiCad 10+ IPC extension mode" (Protocol Buffers IPC, background progress dialog) with fallback to Specctra DSN/SES | OBSERVED (v2.5.0 notes) |
| Telemetry / network | README mentions analytics (disable with `-da`), a public API and MCP server; self-host is optional. Treat the default as "phones home" until `-da` is set and verified | OBSERVED (CLI doc, README); default behaviour on first run = INFERRED |
| Maintainer capacity | README says the maintainer is limiting time to about 4 hours per week and has 4 financial supporters | OBSERVED (README) |
| Own quality data | v2.5.0 notes: on a 1,157-board benchmark, 75.0 % (868) finished with zero DRC violations and 75.4 % (872) fully routed. On 560 routine 2-4 layer boards: 61.6 % clean. Release notes list no diff-pair or length-tuning feature; I did not find a docs statement either way | OBSERVED (numbers); "no diff-pair/length tuning" = not found in docs, so unverified |
| KiCad community view | KiCad does not ship an autorouter; moderator jmk: "No, not in 5. anything, or 6."; marekr: volunteers, no time to maintain one. Users: John_Pateman: for layout-sensitive designs setup "often takes more time than routing the project manually"; Michael_Lee: "High speed, RF or high density - forget about it"; Meterman2026 and TwoSpoons: cleanup of DRC errors outweighs the benefit. No KiCad-staff statement specific to mixed-signal found | OBSERVED (forum.kicad.info thread 30441); official KiCad docs statement: not found |

Safety assessment (INFERRED): reasonable to run. It is a GPL-3.0 open-source project with GitHub-verified release commits and published SHA-256 per asset; it runs on a local file. Risks: single maintainer, optional telemetry, newest release is a month old, so verify the SHA-256 against the release page and pin the version. Output goes through `.ses` import, so it cannot alter your schematic.

Use for / hand-route (SPECULATIVE, consistent with the community statements above):
- Autoroute: low-speed digital (RP2350 GPIO fan-out to DAC/SPI, LEDs, gate buffers, pots/switch lines), jack-to-buffer stubs on the modulation and gate outputs after you lock placement. Always review.
- Hand-route: DAC reference and analog ground return, 16-bit pitch DAC output and op-amp stage, anything carrying the pitch path, power distribution and decoupling loops, USB D+/D- (impedance-controlled pair; I did not verify Freerouting handles diff pairs), crystal, and the SPI/clock lines near the pitch DAC. Pour planes yourself.
- Run with `-inc` for ground/power so planes are yours.

Recommended answer: install the v2.5.0 native macOS arm64 binary (no JRE), verify SHA-256 from the release page, run headless with `-da`, autoroute only the low-speed digital and non-critical nets after placement; hand-route all analog, USB and power.
Next-best: `java -jar freerouting-2.5.0.jar` with Temurin 25 (`brew install --cask temurin@25`, verify the cask name first) rather than the default `temurin` cask (JDK 27).

---

## 2. DAC settling and accuracy for a 1 V/oct pitch output

### Computed numbers (math, no source needed)

| Quantity | Value |
|---|---|
| 1 cent at 1 V/oct | 1000 mV / 1200 = 0.8333 mV = 833.3 uV |
| 1 semitone | 83.33 mV |
| LSB, 10 V span, 16 bit (10 V / 65536) | 152.59 uV = 0.1831 cent |
| 1/2 LSB | 76.3 uV = 0.0916 cent |
| +/-2 LSB | +/-305.2 uV = +/-0.366 cent |
| Codes per semitone | about 546 LSB |
| "Within 1/2 LSB of a full 10 V step" | 10 V / 76.3 uV = 131,072 = 2^17, about 11.8 time constants. For 10 us, tau must be <= 0.85 us (single pole, bandwidth >= about 187 kHz) |
| 10 V in 10 us | 1 V/us slew needed |

### What is musically meaningful

| Item | Finding | Label |
|---|---|---|
| Pitch discrimination | Wikipedia "Cent (music)": a single cent is too small to be perceived between successive notes; one author (Loeffler 2006) says humans distinguish about 5-6 cents; normal adults recognise 25 cents "very reliably" (Peretz & Hyde 2003); student musicians' out-of-tune detection degraded at +/-12 cents (Geringer & Worthy 1999) | OBSERVED (en.wikipedia.org/wiki/Cent_(music)); primary papers not read |
| Primary psychoacoustics source | A search hit (Steinberg forum) says JND about 3 Hz for sine waves; PMC3928243 (Oxenham 2013) did not give a cents figure when queried | Steinberg figure = excerpt only; PMC: not found |
| Doepfer VCO | A-110 page: frequency range about 8 octaves (ca. 15 Hz to 8 kHz); no tracking-accuracy number on the page | OBSERVED; tracking spec: not found |
| Doepfer A-110-1 / other VCO tracking claims | not found in manuals I could open. Thonk t01 DIY VCO: "tuned ... precision of +-1 ..." (excerpt cut off) | not found |
| EIS (open Eurorack spec) bus CV | "1.00 V/octave pitch CV (bus CV), +/-0.3 % of scale" (section 6.6). 0.3 % of 1 V/oct is 3.6 cents per octave of scale | OBSERVED (lzxindustries.net/eis/eis.pdf); cents conversion INFERRED |
| Yarns calibration | Calibrates every volt from -3 V to +7 V against a multimeter; encoder step about 0.2 mV (about 0.24 cent); fast step 6 mV | OBSERVED (pichenettes.github.io Yarns manual) |
| Expert Sleepers ES-9 | DC-coupled outputs, max output about +/-10 V; no cents or mV accuracy figure found. Silent Way has calibration data page (expert-sleepers.co.uk/siwacalibrationdata.html), not opened | OBSERVED (ES-9 page); accuracy: not found |
| Ornament & Crime calibration docs | README fetch returned nothing relevant | not found |
| Settling vs op-amp slew | No source found. Reasoning: a 10 V step into a VCO input only matters as pitch glide (a transient of order of the output stage's settling); op-amp slew, cable capacitance and the VCO's own CV-input lowpass dominate over the DAC's own glitch. Typical op-amp slew figures not cited here | INFERRED |

### Requirement wording that is testable (my proposal, SPECULATIVE as to the numbers; derived from the 5-6 cent JND and the EIS 0.3 % class)

1. Static accuracy: after the on-device calibration, at each of 11 test voltages (0, 1, ... 10 V, or the chosen -3..+7 V octave points) the output measured with a 6.5-digit DMM (10 PLC, 5-minute warm-up, 23 +/- 3 C) is within +/-0.5 mV (+/-0.6 cent) of target. Pass/fail by DMM only.
2. Linearity: across the 10 V span, the straight-line error between calibrated octave points is <= +/-0.5 mV.
3. Dynamic: for a code step from 2.000 V to 3.000 V (1 octave) and from 0 V to 9 V, the output reaches and stays within +/-0.83 mV (1 cent) of the final value within 200 us, with a 1 mV/div scope trace averaged (note: a scope resolves 0.83 mV poorly; use AC-coupled, offset final value, 20 MHz bandwidth limit, 64-sample average). Glitch energy on adjacent-code transitions (e.g. major carry): peak < 2 mV.
4. Drift: 1 hour after warm-up, change <= 0.5 mV.

6.5-digit DMM resolution on a 10 V range is about 10 uV (INFERRED from digit count), well under the 76 uV half-LSB, so the DMM can verify LSB-level claims; the scope cannot.

Recommended answer: drop "10 us to 1/2 LSB at 16 bit"; specify static error <= +/-0.5 mV (about 0.6 cent) at the DMM across the calibrated range, plus a scope check that a 1 V step settles within +/-1 cent in <= 200 us, because the ear tolerates 5-6 cents and the op-amp/cable/VCO path dominates.
Next-best: keep a dynamic check but loosen to +/-1 LSB (+/-153 uV) in 1 ms, measured with a high-resolution scope or a DMM in a burst-sampling mode.

---

## 3. Eurorack power header: shrouded vs unshrouded, 10-pin vs 16-pin

### Doepfer (the original standard)

| Source | Text | Label |
|---|---|---|
| a100t_e.htm (technical details) | -12 V line marked by a coloured (typically red) wire, aligned to the bottom of the bus board "-12V" imprint. Both 10-pin and 16-pin connections carry -12 V, GND, +12 V; 16-pin adds +5 V, CV, Gate. "Pay attention that applying other than the described voltages or changing the polarity will result in the module's instant destruction !" Rule: "red strip down". Page still carries the warning that bus boards with polarized (boxed) headers "force the user to connect the bus cable in a certain direction which may be the wrong one" | OBSERVED (doepfer.de/a100_man/a100t_e.htm) |
| a100_faq.htm (FAQ) | Doepfer started with unboxed headers in 1995 (cost). Boxed headers can force wrong-direction connection on older modules; "Livewire, Plan B, Jomox, Cwejman, MFB and other manufactures" also had wrong-polarity modules. "Nevertheless we decided to change over to boxed pin headers during the year 2019 because this kind of bus connectors established as a kind of standard on the market", with "a corresponding warning notice to each system". Bus board side is always a 16-pin connector even for a 10-pin cable. Modules since about 2015 carry a "RED STRIP" rectangle marking on the PCB. Two orientations of boxed headers exist ("gap at the right side" most common) | OBSERVED (doepfer.de/faq/a100_faq.htm) |
| manual_e.htm | Lists "A-100 Short form manual / safety instruction for cases manufactured until end of 2019 (bus boards with unboxed pin headers)" | OBSERVED |
| a100_cases_e.htm (search excerpt) | September 2019 case text: 8 non-polarized (unboxed) and 12 polarized (boxed) bus connectors | search excerpt only |

### Open specification (EIS, LZX Industries)

| Rule | Text | Label |
|---|---|---|
| BUS-002 | power header is 2x5 or 2x8 pin on 2.54 mm grid | OBSERVED (lzxindustries.net/eis/eis.pdf section 6.4) |
| BUS-005 | a shrouded header "shall be keyed so that, viewed from the mating side with the -12 V end at the bottom, the key gap is on the right" | OBSERVED |
| BUS-004 | marked conductor of the ribbon is -12 V; unshrouded headers rely on the marked conductor | OBSERVED |
| BUS-007 | a module using neither +5 V nor bus CV/gate "may use the 10-pin header" | OBSERVED |
| BUS-009 | module or power supply "shall tolerate reverse polarity at its power header without damage" | OBSERVED |

### What major makers fit

Mutable Instruments, Intellijel, Make Noise, Befaco, Noise Engineering, ALM: **not found** (no build doc, schematic or manufacturer statement retrieved). Two unrelated search excerpts: a product listing mentions "16-pin Eurorack power shrouded headers" and an unidentified module manual (therockstore.com.ar/manuals/1001199.pdf) says a "black plastic shroud" and that Schottky diodes "double-secure the reverse polarity" protection. Not verified beyond the excerpts.

### Failure modes (INFERRED)
- A shrouded keyed header stops reversal at the module-to-cable mate and stops 10-pin cable shifted by one position/offset to the wrong rows.
- It cannot catch: a ribbon built with the red stripe on the wrong end at the other connector (a cable crimped backwards still mates "correctly" to a keyed header only if the connector crimp is also keyed the same; a miswired power-supply header, or an unkeyed power supply end), a cable between a boxed module header and an unboxed legacy bus board (Doepfer's 50 % problem), or modules wired with opposite key polarity (Doepfer notes both exist).
- So a shroud is a convenience; the electrical defence is a reverse-polarity circuit (EIS BUS-009).

Recommended answer: 2x5 (10-pin) shrouded keyed header, gap on the right with -12 V at the bottom (EIS BUS-005), red-stripe silkscreen and "-12V" at pin 1, plus reverse-polarity protection (series Schottky or P-FET) on both rails. Use 10-pin since the module needs neither +5 V nor bus CV/gate (add a 5 V pad only if the RP2350 supply cannot come from +12 V via a regulator).
Next-best: unshrouded 2x5 with red-stripe silkscreen, the pre-2019 Doepfer-compatible choice, with the same reverse protection.

---

## 4. Voltage conventions

### (a) Pitch reference and range

| Source | Finding | Label |
|---|---|---|
| Doepfer a100t_e.htm | "CV is not an absolute but a relative parameter. A certain CV value (e.g. +1.0V) is not assigned to an absolute pitch"; 1 V = 1 octave | OBSERVED |
| Doepfer A-190-4 | CV1 about -3 V to +10 V, CV2 0 to +10 V; default reference note "C2" resp. MIDI note 24 (tune sets the offset of the reference note); the page itself does not state which note is 0 V | OBSERVED (doepfer.de/a1904.htm; A190_4_man.pdf) |
| Doepfer A-190-1 | CV output 0 to +5 V (DAC 1 12-bit, DAC 2 7-bit) | OBSERVED (doepfer.de/a190.htm) |
| Mutable Yarns | calibrates -3 V to +7 V in 1 V steps (a 10 V span) | OBSERVED (Yarns manual); note-to-0 V mapping: not found on the page |
| Expert Sleepers ES-9 | outputs up to about +/-10 V DC-coupled; 0 V reference note: not found | OBSERVED / not found |
| Arturia, Korg SQ-1, Moog, Make Noise | not found |
| Wikipedia CV/gate | 1 V/oct popularised by Moog; trigger voltage "differs among brands, from 2V to 10V"; Korg/Yamaha used Hz/V and inverted (S-trigger) gates | OBSERVED (en.wikipedia.org/wiki/CV/gate) |

Convention summary: the common sets are MIDI note 24 (C1 in some naming, C2 in Doepfer's) or about note 36 = 0 V; I could not verify a single majority. A 10 V window starting at -3 V (Yarns, A-190-4 CV1 minimum) covers about MIDI notes 0 to 120 when 0 V is note 36 (SPECULATIVE; arithmetic: 10 octaves x 12 = 120 semitones).

Pitch default: 0 V = MIDI note 36 (C2 in the "middle C = C4/note 60" naming), range -3 V to +7 V, which covers MIDI notes 0 to 120. Make the reference a stored, user-editable offset because every source above treats it as tunable.

### (b) Modulation CV ranges
Doepfer: LFOs typically -2.5 V to +2.5 V (5 Vpp), ADSRs 0 to +8 V, audio about +/-5 V (10 Vpp). EIS Bus CV is pitch only. OBSERVED (a100t_e.htm). Other modules' ranges: not found.
Default: unipolar 0 to +8 V for envelope-like modulation, with a per-output mode for bipolar -5 V to +5 V (10 V span, same DAC scaling as pitch).

### (c) Gate level
Doepfer: gate "usually" 0/+5 V; "any voltage beyond about +3V is treated as high (e.g. +5V, +8V, +10V, +12V will work)" and "any voltage below 1V is treated as low"; all A-100 modules withstand up to +12 V. OBSERVED (a100t_e.htm). A-190-4 gate default +5 V, +12 V via jumper JP4. OBSERVED. EIS: bus gate high +4 V to +12 V, low <= +0.5 V; listener high >= +3 V, low <= +1 V. OBSERVED. Gear needing higher gates (Moog, Korg, Buchla formats): only the Wikipedia statement that trigger levels range 2 V to 10 V by brand; specific modules: not found.
Default: +5 V (within EIS 4-12 V output window); offer a hardware option or firmware-selectable +8 V only if a test module needs it.

### (d) Trigger length
Doepfer pages read do not give a generic trigger length (A-190-4 manual: not stated). Yarns: trigger duration is user-set (milliseconds), not a fixed convention. Standard ms value: not found.
Default: 5 ms trigger (SPECULATIVE; long enough for slow modules, short enough for 16th notes at 300 BPM = 50 ms), user-adjustable 1-20 ms.

### (e) Clock resolution
Doepfer A-190-4: MIDI clock pulses are 1/96th notes (i.e. 24 per quarter note); divider settings include 1 (96 clocks/note), 6 (16 clocks per note), 12 (8), 24 (4). OBSERVED (A190_4_man.pdf). A search excerpt of a MIDI manual lists a 24 PPQN clock and a 1 PPQN clock output (a different product, not read). Common analog clocks per quarter note: not verified.
Default: expose 24 PPQN base and divide to 1, 2 (8th), 4 (16th) PPQN in firmware; reset pulse on MIDI Start/Continue.

Recommended answer: pitch 0 V = MIDI note 36, -3 V to +7 V; modulation 0 to +8 V (bipolar -5 to +5 V optional); gate +5 V; trigger 5 ms (adjustable); clock 24 PPQN with divisions.
Next-best: 0..+8 V pitch only if you want to match Doepfer-style "0 V = lowest key", at the cost of 2 fewer octaves.

---

## 5. USB and MIDI SysEx identity

### (a) USB VID/PID

| Option | Finding | Label |
|---|---|---|
| USB-IF Vendor ID | USD 5,000 (annual membership incl. VID), USD 3,500 two-year non-member logo licensee (VID extra if not assigned), or USD 6,000 for a VID alone | OBSERVED (usb.org/getting-vendor-id, extraction) |
| Raspberry Pi PIDs under VID 0x2E8A | github.com/raspberrypi/usb-pid: assignment table (e.g. 0x0003 RP2040 boot, 0x000F RP2350 boot, 0x10AE Datanoise PicoADK v2 RP2350). To request: application form linked from the README; one may "reserve an allocation before making a new product public" but must submit a PR adding the product when public or lose the allocation. Eligibility conditions, cost: not found in the README text (extraction returned none) | OBSERVED / not found |
| pid.codes (VID 0x1209) | free for open-source projects. Conditions: public source repo, modifiable PCB design files and/or source code, recognised open-source or OSHW licence with a LICENSE file; both hardware and software must be licensed if both involved; "You may request any number that is not in use, except those reserved (0xxx and 1xxx)"; may ask for justification | OBSERVED (pid.codes/howto/) |
| Raspberry Pi default/test PIDs | I did not find a rule that allows shipping with default/example PIDs; the Pi example VID/PID are for the SDK examples. Whether prototype use is "acceptable": not found | not found |

### (b) MIDI SysEx manufacturer ID (MIDI Association policy, effective 2025-10-15)

| Option | Finding | Label |
|---|---|---|
| Corporate member | from USD 600/year, includes a SysEx ID | OBSERVED (midi.org/new-midi-association-sysex-id-policies-as-of-oct-15-2025) |
| Paid SysEx ID holder | USD 240, one-time fee, non-voting; IDs now permanent and owned in perpetuity (no annual renewal) | OBSERVED |
| 0x7D | non-commercial (schools, research), "not to be used on any product released to the public" | OBSERVED |
| 0x7C (new in 2025) | free; may be used on products released to the public only if the product does not receive financial gain directly or indirectly; only for UMP endpoint discovery and MIDI-CI discovery; NOT for system-exclusive messages with custom data format | OBSERVED |
| What small makers do | not found beyond the forum excerpt that 0x7D has been the usual workaround | search excerpt only |

Implication (INFERRED from the quoted rules): a shipped, sold module with its own SysEx command set may not use 0x7D or 0x7C; it needs a purchased ID (USD 240). The older forum figures USD 260/280 per year are superseded.

Recommended answer: prototype: VID 0x2E8A with a PID from the Raspberry Pi allocation request (or the RP2350 test PID during bench work only), SysEx ID 0x7D. Shipped product: PID from the Raspberry Pi allocation (confirm conditions in the form) or pid.codes if the design is open source; buy a MIDI Association SysEx ID (USD 240 one-off).
Next-best: if the hardware is not open source and the Pi allocation is not granted, buy a USB-IF VID (about USD 6,000) only when you need your own VID; otherwise stay on pid.codes.

---

## 6. iOS / iPadOS as a host

| Question | Finding | Label |
|---|---|---|
| CoreMIDI sysex | `MIDISendSysex` exists, "Asynchronously sends a single system-exclusive (SysEx) event", iOS 4.2+/iPadOS 4.2+ | OBSERVED (search excerpt of developer.apple.com/documentation/coremidi/midisendsysex(_:)); behaviour with USB devices tested: not found |
| Class-compliant USB MIDI works on iPad | inMusic support page says class-compliant devices connect to Windows, Mac, "or to your iPad"; RME Babyface Pro FS manual notes iPad needs CC mode, USB-C iPad Pro "offers full USB connectivity" | search excerpts only |
| USB-C iPad accessory current (Apple Accessory Design Guidelines, section 24.1) | default 900 mA on most listed iPad Air/Pro/mini models, 500 mA on iPad (10th generation); more via USB-C current/PD (1.5 A or 3.0 A) | OBSERVED (search excerpt of developer.apple.com/accessories/Accessory-Design-Guidelines.pdf) |
| Lightning accessory current, bMaxPower / self-powered declaration handling | not found (extraction found nothing) | not found |
| Real-world failure mode | users get "Cannot Use Device ... requires too much power" with bus-powered MIDI keyboards (e.g. Akai MPK mini via Lightning camera adapter, Apple Community thread 250636589 title) | OBSERVED (search excerpt, title/snippet) |
| MFi need for class-compliant MIDI | not found (Apple guidelines extraction did not mention it) | not found |
| 0 mA / 100 mA self-powered accepted | not found; INFERRED that a self-powered device declaring low bMaxPower avoids the "too much power" alert, since that alert is a function of declared current vs available current | INFERRED |

The module is powered from the Eurorack +12 V rail, so it can declare itself self-powered with small bMaxPower (SPECULATIVE; verify with a physical iPad). Eurorack power is not available through the USB-C port, so the iPad is only a data host.

Recommended answer: do not make iOS a v1 requirement; design the descriptor as self-powered with bMaxPower as low as the TinyUSB/RP2350 config allows (e.g. 50 mA or 100 mA) so it is likely to work, and put "iPad: test post-v1" on the roadmap.
Next-best: accept iPad USB-C as a stretch requirement for v1 gated by one bench test (module on an iPad (10th gen), 500 mA class) before release.

---

## 7. Fail-safe when the computer disappears

| Item | Finding | Label |
|---|---|---|
| MIDI 1.0 active sensing | status 0xFE: "intended to be sent repeatedly ... Use of this message is optional. When initially received, the receiver will expect to receive another Active Sensing message each 300ms (max), and if it does not then it will assume that the connection has been terminated. At termination, the receiver will turn off all voices and return to normal (non-active sensing) operation." | OBSERVED (midi.org/summary-of-midi-1-0-messages, search excerpt of that URL) |
| Doepfer A-190-4 | Controller 123 (All Notes Off): gate turned off, notes cleared, "Control voltages remain at the level at which they were set at last". MIDI Stop sets the Reset output high | OBSERVED (doepfer.de/a100_man/A190_4_man.pdf) |
| Yarns, ES-9/FH-2, others | behaviour on MIDI loss: not found (Yarns manual extraction: not stated) | not found |
| USB host disappearance | USB suspend/disconnect detection is device-side (TinyUSB); the MIDI spec rule applies only to a connected TRS/DIN link that actually sends 0xFE | INFERRED |

The owner's behaviour ("pitch holds, modulation slews to 0 V in 50 ms, gates low") matches the A-190-4 for gates and pitch. The 50 ms modulation slew-to-0 V has no documented precedent in what I found; it is a design choice.

Recommended answer: on USB disconnect, suspend, or 300 ms without host heartbeat (or without 0xFE once active sensing has started on the TRS input): gates low immediately, pitch holds, modulation slews to 0 V in 50 ms, clock stops, reset line asserted; document it as "like All Notes Off in the A-190-4, plus modulation return to rest".
Next-best: hold everything (including modulation) and drop only the gates.

---

## 8. Naming: "Kiln" (hardware) and "BeatOven" (software)

| Item | Finding | Label |
|---|---|---|
| Vitric Audio "Kiln Synthesizer" | exists: wavetable synth plugin for macOS and Windows (AU, VST3, AAX), sold at USD 80 per Sonicstate (2026-09-14 article), with 683 presets and a free 3-day trial; v1.1.3 on its downloads page; site text says other names are "trademarks of their ... owners" (no registration statement for Kiln seen) | OBSERVED (vitricaudio.com/kiln, sonicstate.com/news/2026/09/14/vitric-audio-releases-kiln-synthesizer, kvraudio.com product page; price from search excerpt) |
| USPTO TESS / current trademark search (IC 009, 015) | could not be queried with my tools (JavaScript search UI); no results returned for "KILN" trademark queries | not found |
| Other hits | Fleetwood Mac album "Kiln House" (unrelated); AMACO (ceramics kilns, unrelated) | OBSERVED (search results) |
| Collision strength | "Kiln" is a recently launched, same-field product name (music software, class 009 goods) in plugin form, announced 2026-09. A hardware synth module named Kiln in class 009/015 is likely to be confusable (INFERRED) because both are synth/music-production goods | INFERRED |
| BeatOven vs Beatoven.ai | the task note says Beatoven.ai is an unrelated AI-music company; I did not search it independently | not verified |

Recommended answer: treat "Kiln" as a working name only; run a USPTO search by hand (classes 009, 015, 041) and an EUIPO/UKIPO check before printing panels, and prefer a distinctive name for the shipped product. Keep "BeatOven" for software only after checking Beatoven.ai and a trademark search.
Next-best: keep "Kiln" for the hardware but add a distinguishing mark (e.g. "Kiln CV" / maker prefix), accepting residual risk; get counsel's opinion before commercial launch.

---

## Not verified (summary)
- Freerouting: notarisation/code-signing of the dmg; diff-pair and length-tuning support (no statement found); `brew` cask name `temurin@25`; default telemetry behaviour; official KiCad documentation or staff statement on mixed-signal autorouting.
- DAC: no datasheet-derived settling numbers; no VCO tracking claims (Doepfer, others) found; no Expert Sleepers or Ornament & Crime accuracy figures; primary psychoacoustics paper not read (Wikipedia citing Loeffler 2006, Peretz & Hyde 2003).
- Power header: what Mutable Instruments, Intellijel, Make Noise, Befaco, Noise Engineering, ALM fit; reverse-protection approaches for those makers.
- Voltage conventions: which note is 0 V for Doepfer A-190, Expert Sleepers, Yarns, Arturia, Korg SQ-1, Moog, Make Noise (only A-190-4's default reference note C2 / MIDI 24); modules needing higher gates; trigger length and analog clock PPQN conventions.
- USB: Raspberry Pi PID allocation eligibility/cost; whether default/test PIDs are acceptable; USB-IF terms on unlicensed use.
- MIDI ID: what small makers actually do.
- iOS: Lightning power limits, bMaxPower/self-powered handling, any MFi need, SysEx via USB on iOS tested.
- Failure behaviour: Yarns, Expert Sleepers, other manuals.
- Trademark: USPTO/EUIPO search results for "Kiln"; Beatoven.ai.
