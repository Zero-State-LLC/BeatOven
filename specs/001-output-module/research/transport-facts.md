# Transport and MCU fact sheet (Output Module)

Gathered 2026-11-11/12. Labels: **OBSERVED** = read at the cited URL this session; **INFERRED** = reasoning (basis stated); **SPECULATIVE** = guess. "No published measurement found" = searched, nothing citable.
Note: some page text was read through a summarising fetch tool; quotes marked "(summary)" were not read verbatim. Primary-source gaps are listed in section 7.

## 1. Transports

### 1.1 Summary table

| Transport | Latency/jitter mechanism | Wire timestamps | Determinism | BOM / cert |
|---|---|---|---|---|
| (a) USB-MIDI 1.0, FS | Device polled on 1 ms frames (INFERRED from USB FS spec; see 1.2). Host side adds OS scheduling | None | Host-scheduled; +/-1 ms class | USB connector, MCU USB; no extra IC |
| (a) USB-MIDI 1.0, HS | 125 us microframes (INFERRED, USB 2.0 spec knowledge, not fetched) | None | Better poll granularity; OS jitter still dominates | HS needs ULPI PHY on most MCUs (1.3) |
| (b) USB-MIDI 2.0 / UMP | Same USB timing as (a); adds optional JR Timestamps | Optional JR, 16-bit, 1/31250 s ticks | Receiver can re-time events | Same as (a) |
| (c) DIN/TRS MIDI 31.25 kbaud | 320 us/byte (arithmetic below); 3-byte message ~0.96 ms | None | Fully deterministic wire, serial blocking | Opto input + UART; DPT uses HCPL-0631 |
| (d) I2C "ii" | Leader-initiated polled bus; no timing guarantees published | None | Single leader only supported | Pull-ups to 5 V; short cables |
| (e) UART / USB-CDC + CBOR | USB-CDC rides same 1 ms FS frames; UART timing set by baud | None (CBOR frame carries what we define) | We control framing; host still schedules | No class-compliance constraint on our side |
| (f) Wi-Fi OSC/UDP | Contention, power-save, retries; jitter reported 1-5 ms and worse | OSC bundles have NTP timetags (INFERRED, OSC 1.0 spec knowledge, not fetched) | Worst of the six | Radio module, RF cert |

### 1.2 USB timing and published jitter

| Claim | Label | Source |
|---|---|---|
| Bome engineers: "USB is inherently worse than MIDI-DIN (due to its 1ms-scheduling), it stays +/- 1 millisecond"; "USB Input is polled once per millisecond, hence +/-500us jitter"; on Windows many sequencers run at 1 ms resolution | OBSERVED (vendor forum post, 2018-02-05; not a controlled study) | https://forum.bome.com/t/bomebox-midi-jitter/884 |
| Oscilloscope test, REAPER 200 BPM 16ths (75 ms intervals), interval-to-interval deviation, **MIDI DIN outputs via USB-connected interfaces**: macOS (Mavericks) RME UCX II max 0.61 ms (early -0.26/late +0.36 ms); macOS Emagic Unitor 8 0.76 ms; Debian Linux Unitor 8 1.04 ms; Debian Linux UCX II (class-compliant mode) 1.41 ms; Windows 10 UCX II 3.05 ms (late +2.40 ms); Atari ST reference 0.25 ms. Metric is spread of consecutive-interval error, not RMS or p99 | OBSERVED (blog post; interface-to-DIN path, so includes DIN byte time and interface firmware) | https://www.donsolaris.com/?p=4333 |
| Software measuring DAW-to-DIN MIDI clock: one user posts 0.038 ms RMS (max 0.59 ms) | OBSERVED (forum search snippet only; thread page not read) | https://gearspace.com/threads/free-software-measures-midi-latency-and-jitter.957824/page-6 |
| USB-MIDI jitter on iOS/iPadOS | no published measurement found | n/a |
| Direct measurement of USB-MIDI device-to-jack latency for our target (p99 <= 2 ms) | no published measurement found | n/a |
| INFERRED: A 1 ms-polled transport alone consumes about half of a 2 ms p99 budget, before OS timestamping jitter (above shows 0.6-3 ms spreads end to end). Meeting <= 2 ms p99 and <= 100 us RMS clock jitter without wire timestamps therefore relies on host-side scheduling, or on timestamps plus a device-side playout buffer. | INFERRED | basis: figures above |

### 1.3 MIDI timestamps

| Claim | Label | Source |
|---|---|---|
| USB-MIDI 1.0 events are 4-byte packets (cable/CIN header + 3 bytes); no timestamp field | INFERRED (USB-MIDI 1.0 class spec knowledge; TinyUSB doc confirms 4-byte packets exist: "4-byte USB-MIDI 1.0 event packets") | https://docs.tinyusb.org/en/latest/reference/class/midi.html |
| MIDI 2.0 UMP adds optional Jitter Reduction: JR Clock (sender's current time, sent independently) and JR Timestamp (can be prepended to any MIDI 1.0 or 2.0 message) | OBSERVED | https://midi.org/details-about-midi-2-0-midi-ci-profiles-and-property-exchange-updated-june-2023 |
| JR Timestamp is a 16-bit count in units of 1/31,250 s (31.25 us, about 32 us); utility message type 0x0 | OBSERVED (search snippet of field guide + Italian monograph snippet; the field-guide page itself not opened) | https://midi.community/docs/midi-2/ ; https://air.unimi.it/retrieve/dfa8b9a8-57d2-748b-e053-3a05fe0a3a96/27-Monografia-507-1-10-20211012.pdf |
| A forum post quoting spec M2-104-UM sections 4.8.2/4.8.3 says resolution is 32 us and that the receiver adds a few ms of delay then plays by timestamp | OBSERVED (forum, secondary) | https://forums.musicplayer.com/topic/178223-midi-20-timing-resolution-more-info/ |
| INFERRED: 16 bits x 31.25 us wraps every 2.048 s, so JR Clock messages must be sent more often than that. | INFERRED (arithmetic: 65536 x 31.25 us = 2.048 s) | n/a |
| INFERRED: 31.25 us resolution is finer than the 100 us RMS jitter target, but JR only helps if the receiver delays playout by more than the transport's worst-case jitter (adds latency; conflicts with the 2 ms budget unless jitter is below it). | INFERRED | basis: forum description above |
| Whether any shipping host stack (CoreMIDI, ALSA, Windows MIDI Services) generates JR timestamps on USB output | no published measurement found / not verified | n/a |

### 1.4 DIN/TRS MIDI timing

| Claim | Label |
|---|---|
| 31.25 kbaud, 10 bits per byte (start + 8 data + stop) gives 320 us per byte; 3-byte note message = 960 us; clock-resolution unit 1/31250 s = 32 us (UMP JR tick equals one bit time) | INFERRED (arithmetic; bit-time coincidence confirmed by https://forums.musicplayer.com/topic/178223-midi-20-timing-resolution-more-info/ , OBSERVED) |
| Throughput cap about 3125 bytes/s, so about 1040 three-byte messages/s; a mod-CV stream of 4 channels at 1 kHz would not fit | INFERRED (arithmetic) |
| Atari ST DIN reference jitter 0.25 ms max, 0.03 ms average on the same bench | OBSERVED (https://www.donsolaris.com/?p=4333) |
| Opto input: Patch SM-based DPT uses HCPL-0631 (6N138/H11L1 class not used there); includes Type A/B auto-sense circuit | OBSERVED (https://github.com/joemisra/dpt , BOM lists U8 HCPL-0631; dpt-documentation.md says optically isolated HCPL-0631) |
| 6N138 / H11L1 as standard MIDI-spec optocouplers | SPECULATIVE (from general knowledge, not verified this session) |

### 1.5 Host OS support

| Host | Fact | Label | Source |
|---|---|---|---|
| macOS (CoreMIDI) | MIDI 2/UMP API available iOS/iPadOS/Mac Catalyst 14.0+; "By default, Core MIDI adopts the MIDI 2 specification and transparently converts" to the destination's protocol; legacy destinations receive MIDIPacketList, MIDI 2 destinations MIDIEventList | OBSERVED | https://developer.apple.com/documentation/coremidi/incorporating-midi-2-into-your-apps |
| macOS | Whether CoreMIDI uses JR timestamps on the USB wire (vs host-side MIDITimeStamp scheduling) | not verified | n/a |
| Linux (ALSA) | UMP/MIDI 2.0 in ALSA since kernel 6.5; USB-audio driver prefers MIDI 2.0 interface (altset 1) by default; `midi2_enable=0` falls back to MIDI 1.0; for older devices builds topology from Group Terminal Blocks | OBSERVED | https://docs.kernel.org/sound/designs/midi-2.0.html (summary) ; https://github.com/raspberrypi/linux/issues/7474 (says upstream since 6.5; Raspberry Pi OS kernels ship with UMP options disabled) ; https://midi.org/midi-2-0-now-available-in-openwrt |
| Windows | Windows MIDI Services in-box in Windows 11 25H2 and later with new USB class driver (USB MIDI 1.0 and 2.0); developer API in preview; known-issues post exists; users report SysEx splitting after a 2026 update (KB5077181/KB5074105) | OBSERVED | https://microsoft.github.io/MIDI/ ; https://github.com/microsoft/MIDI/releases ; https://learn.microsoft.com/en-us/answers/questions/5828318/usb-midi-sysex-messages-split-after-windows-update |
| iOS/iPadOS: class-compliant MIDI | Needs Apple USB camera adapter (iPhone/iPad connection); class-compliant MIDI devices work with the app via CoreMIDI | OBSERVED (adapter requirement from search results only) | https://onsongapp.com/store/cck/ ; https://support.apple.com/en-us/111811 |
| iOS/iPadOS: bus power limit | no figure found in this session | not verified | n/a |
| iOS/iPadOS: generic USB CDC serial for apps | Apple DTS (via forum thread summaries): no iOS API for generic USB peripherals; MFi + ExternalAccessory is the supported route; DriverKit (iPadOS only) can match CDC-ACM with entitlements; iPhone not covered | OBSERVED (forum threads, search summary, not read in full) | https://developer.apple.com/forums/thread/819129 ; https://developer.apple.com/forums/thread/826070 |

### 1.6 SysEx over USB-MIDI

| Claim | Label | Source |
|---|---|---|
| UMP/USB-MIDI 1.0 SysEx travels as CIN 0x4/0x5/0x6/0x7 packets, 3 payload bytes per 4-byte packet (so 75% payload efficiency); no protocol size limit seen in the TinyUSB converter doc | OBSERVED (conversion logic) / INFERRED (efficiency arithmetic) | https://github.com/midi2-dev/tusb_ump |
| Large single SysEx buffer (4104 bytes) failed on Linux/macOS with a cheap class-compliant interface; workaround was 128-256 byte chunks with 50-60 ms gaps (<25 ms still dropped). That failure was caused by the DIN side behind the interface, not USB | OBSERVED (single issue thread) | https://github.com/asb2m10/dexed/issues/157 |
| Windows: SysEx packets "split into multiple smaller packets" after updates KB5077181 and KB5074105 | OBSERVED (Microsoft Q&A, snippet) | https://learn.microsoft.com/en-us/answers/questions/5828318/usb-midi-sysex-messages-split-after-windows-update |
| macOS: sending moderate SysEx (1330 bytes) over USB had problems in JUCE thread | OBSERVED (snippet only, thread not read) | https://forum.juce.com/t/problem-with-sysex-transfer-over-usb-midi-on-mac/9830 |
| Continuous SysEx streaming throughput measurements on macOS/Linux/iOS | no published measurement found | n/a |
| INFERRED: Continuous real-time events inside SysEx would block channel messages on the same cable (SysEx may be interrupted only by realtime bytes in MIDI 1.0), so SysEx is a poor carrier for a timed event stream; UMP Data64/SysEx8 on a separate group is cleaner. | INFERRED | basis: MIDI 1.0 SysEx rules (spec knowledge) |

### 1.7 Device-side MIDI 2.0 stack

| Claim | Label | Source |
|---|---|---|
| TinyUSB has a MIDI 2.0 device driver: enable `CFG_TUD_MIDI2`, descriptor `TUD_MIDI2_DESCRIPTOR` with alt setting 0 (USB-MIDI 1.0 fallback) and alt setting 1 (native UMP); `tud_midi2_ump_read/write` use 32-bit words; handles UMP Stream discovery/negotiation; host-side calls (`tuh_midi2_*`) also exist; example "MIDI 2.0 Song Sender" | OBSERVED | https://docs.tinyusb.org/en/latest/reference/class/midi.html ; https://docs.tinyusb.org/en/latest/examples/device/midi2_device.html |
| The page lists no JR timestamp helper in the device API | OBSERVED (absence in the page text read) | same |
| AmeNote/midi2-dev `tusb_ump` is a separate TinyUSB UMP device+host driver with MIDI 1.0 <-> UMP conversion | OBSERVED | https://github.com/midi2-dev/tusb_ump |
| Zephyr has UMP/MIDI 2.0 definitions (doxygen group `ump112`, "Device Drivers > Audio > MIDI2"); the page does not mention JR timestamps | OBSERVED | https://docs.zephyrproject.org/latest/doxygen/html/group__ump112.html (summary) |
| Whether TinyUSB MIDI2 is stable vs experimental, and which release added it | not verified | n/a |

### 1.8 I2C "ii" (Teletype)

| Claim | Label | Source |
|---|---|---|
| 3-wire bus (GND, SDA, SCL), pulled up to 5 V; keep cables short to avoid dropped data | OBSERVED | https://monome.org/docs/ansible/i2c/ |
| Leader initiates; multiple leaders not officially supported (risk of lock-ups needing power cycle); multiple followers allowed | OBSERVED | same |
| I2C standard speeds 100 kbit/s standard, up to 400 kbit/s fast, 1 Mbit/s beyond | OBSERVED (spec snippet) | https://www.nxp.com/documents/user_manual/UM10204.pdf |
| ii message latency/jitter figures | no published measurement found | n/a |
| INFERRED: Teletype is the leader, so a host computer cannot push a timed stream to an ii follower without a bridge; ii has no timestamps; Patch SM exposes I2C1 at 3.3 V (needs level shift to 5 V pull-ups). | INFERRED | basis: monome doc + Patch SM datasheet pins B7/B8 "0 to 3V3" |

### 1.9 UART / USB-CDC carrying CBOR, and Wi-Fi

| Claim | Label | Source |
|---|---|---|
| USB-CDC rides the same USB frame schedule as USB-MIDI | INFERRED (USB FS frame knowledge) | n/a |
| iOS cannot use CDC without MFi/DriverKit (see 1.5) | OBSERVED | forum threads above |
| Wi-Fi OSC round-trip jitter 1-5 ms (Mitchell et al. 2014, cited in NIME 2016 paper); NIME 2020 WiFi sensor paper reports "tens of milliseconds" with some values over 100 ms; Pipo vendor reports about 5 ms WiFi OSC vs about 3 ms native USB MIDI | OBSERVED (all via search-result summary; underlying papers not opened) | https://www.nime.org/proceedings/2020/nime2020_paper14.pdf ; https://www.crowdsupply.com/pipo-interfaces/pipo/updates/all-about-open-sound-control-osc |
| McLaren Labs: RTP-MIDI over dedicated Ethernet has small uniform flight time; over WiFi large and variable (no figures) | OBSERVED (snippet) | https://mclarenlabs.com/blog/2024/08/31/rtpmidi-version-2-0-latency-adjustment/ |
| Radio module, regulatory/RF certification impact on a Eurorack product | SPECULATIVE (general knowledge; no source read). Patch SM itself is FCC Class A certified, which this does not cover for a radio add-on | Patch SM datasheet FCC section |

## 2. MCU candidates

### 2.1 Capability table

| MCU | USB device | I2S / SPI | On-chip DAC | Timers | Toolchains | Label |
|---|---|---|---|---|---|---|
| RP2040 | USB 1.1 FS (INFERRED, known; not fetched this session) | PIO state machines (programmable) | None | 1 us system timer (INFERRED, not fetched) | pico-sdk, TinyUSB, Zephyr, embassy-rp (INFERRED) | product page read but text yielded no specs |
| RP2350 | "1 x USB 1.1 controller and PHY, with host and device support"; 12 PIO state machines; 520 KB SRAM; dual M33 or Hazard3 @ 150 MHz; 4/8 ADC channels | PIO | None listed | not read | same (INFERRED) | OBSERVED (https://www.raspberrypi.com/products/rp2350/) |
| STM32G474 | "USB 2.0 full-speed interface with LPM and BCD"; no HS; Active, volume production | "Four SPIs ... two with multiplexed half duplex I2S" | "seven DAC channels (3 external and 4 internal)", 12-bit | HRTIM 184 ps resolution; 17 timers | STM32Cube, TinyUSB, Zephyr, embassy-stm32 (INFERRED) | OBSERVED (https://www.st.com/en/microcontrollers-microprocessors/stm32g474re.html, summary) |
| STM32H743VI | not stated in the text read | not read | "2x 12-bit D/A converters (1 MHz)"; Ethernet MAC with DMA; Active | not read | same | OBSERVED (https://www.st.com/en/microcontrollers-microprocessors/stm32h743vi.html, summary) |
| STM32H723VG | "USB 2.0 high-speed/full-speed ... on-chip FS PHY and ULPI for external HS PHY"; 550 MHz M7; Active | not read | not read | not read | same | OBSERVED (https://www.st.com/en/microcontrollers-microprocessors/stm32h723vg.html, summary) |
| STM32H750 (Daisy basis) | HS needs external ULPI PHY (INFERRED from H723 sibling description above); Patch SM exposes only USB D+/D- pins | I2S to codec used on board | 2 x 12-bit (Patch SM CV out) | not read | libDaisy (C++), DaisySP, Arduino, Rust crate `daisy` (OBSERVED crate exists: https://zlosynth.com/daisy/seed/daisy/) | OBSERVED for Patch SM facts, INFERRED for MCU-level |

### 2.2 Cost and availability (LCSC, USD, qty tiers as shown)

Prices change per fetch and per supplier; DigiKey/Mouser pages did not render usable tier tables here (a DigiKey RP2040 page fetch exceeded size limits and was not parsed). Mouser figures are search-result snippets only.

| Part | Qty 10 | Qty 100 | Stock | Page, date | Label |
|---|---|---|---|---|---|
| RP2040 | $1.0093 | $0.8656 | 85,714 | https://www.lcsc.com/product-detail/C2040.html (cached 2026-11-10) | OBSERVED |
| RP2350A QFN-60 | $1.2309 | $1.1599 | 5,465 | https://www.lcsc.com/product-detail/C42411118.html (2026-11-12) | OBSERVED |
| STM32G474RET6 | $11.5694 / $10.5282 (two price columns on page) | $9.8557 / $8.9687 | 263 | https://www.lcsc.com/product-detail/C521608.html (2026-11-12) | OBSERVED |
| STM32G474RET3 (Mouser) | not shown | $7.86 | 25 in stock, 10,560 on order | https://www.mouser.com/c/semiconductors/embedded-processors-controllers/microcontrollers-mcu/arm-microcontrollers-mcu/?m=STMicroelectronics&program%20memory%20size=512%20kB&series=STM32G4 (search snippet) | OBSERVED (snippet) |
| STM32H743VIT6 | $9.1486 | $7.507 | 6 (very low) | https://www.lcsc.com/product-detail/C114409.html (2026-11-12) | OBSERVED |
| STM32H750VBT6 | $5.88 | $4.7899 | 9,454 | https://www.lcsc.com/product-detail/C404010.html (2026-11-12) | OBSERVED |
| STM32H723VGT6 | no price found | no price found | n/a | n/a | not found |

Supply and lifecycle:
- RP2350: "will remain in production until at least January 2045" (OBSERVED, raspberrypi.com page above). RP2040 longevity statement: not read.
- STM32G474RE, H743VI, H723VG: product status "Active", "in volume production" with ST 10-year longevity program link (OBSERVED, ST pages above).
- H743VIT6 on LCSC had 6 units in stock; G474RET6 263 (OBSERVED, above). INFERRED: STM32 supply is lumpier than RP parts; check franchised distributors before committing.

### 2.3 Daisy Patch Submodule (Patch SM)

| Spec | Value | Label | Source |
|---|---|---|---|
| MCU | "ARM Cortex-M7 MCU, running at 480MHz"; STM32 (STM32H750-class per brief, exact part not read) | OBSERVED / unverified part number | https://daisy.audio/products/patch-submodule (redirect target of electro-smith.com/daisy/patch-sm) |
| Memory | 64 MB RAM (page also says "65MB"); variants listed 65MB / 1MB | OBSERVED | same |
| Audio | 96 kHz / 24-bit stereo; marketing page says "24-bit / 192kHz" (conflict) ; codec PCM3060 per Rust crate docs; DPT README says PCM3080, DPT product page says WM8731 (three-way conflict) | OBSERVED (conflicting) | https://zlosynth.com/daisy/seed/daisy/ ; https://github.com/joemisra/dpt ; https://dsp.coffee/products/product |
| CV outputs | 2 (CV_OUT_1 on PA4, CV_OUT_2 on PA5), **12-bit**, 0 to 5 V, 100 ohm output impedance | OBSERVED | https://daisy.nyc3.cdn.digitaloceanspaces.com/products/patch-sm/ES_Patch_SM_datasheet_v1.0.5.pdf |
| Gate outs | 2 (PC14, PC13), 0-5 V | OBSERVED | datasheet |
| Gate ins | 2 | OBSERVED | datasheet |
| CV ins | 12 inputs, 16-bit bipolar CV/pot: CV_1..CV_8 at -5 to +5 V plus ADC_9..ADC_12 at 0-3.3 V | OBSERVED | datasheet; Daisy page |
| Other | SD card (SDMMC), UART, I2C1 (3.3 V), SPI2, USB D+/D- (PB14/PB15) pins; "USB MIDI Capable"; "USB Firmware Flashing" | OBSERVED | datasheet |
| Size | 68 mm x 40 mm technical drawing; mates via 2x5 2.54 mm headers; "can be installed on modules as small as 8HP" | OBSERVED | datasheet |
| Price | $39.99 at qty 1 on one fetch ($34.99 on a variant column), qty 100 $38.99 or $33.99 or $38.08 depending on fetch/column; qty 10 not tiered; "Out of Stock - 3,000 Incoming", 1,900 in production for mid-January 2027; pages/daisy-patch-submodule says "Now available from $31.99" | OBSERVED (internally inconsistent across fetches) | https://daisy.audio/products/patch-submodule ; https://daisy.audio/pages/daisy-patch-submodule (2026-11-12) |
| Compliance | FCC Class A, EN 55032/55035, REACH, RoHS documents linked | OBSERVED | https://docs.daisy.audio/hardware/PatchSM/ (as embedded in product page) |
| Meets ">= 16-bit pitch DAC, >= 4 CV outs" without external DACs? | **No**: 2 outputs, 12 bit | INFERRED (count 2 < 4 and 12 bit < 16 bit; resolution calc below) | datasheet |

Calc for the row above (INFERRED, arithmetic): 5 V / 4096 = 1.22 mV per step; at 1 V/oct that is 1.22 mV x 1200 cents/V = about 1.46 cents per step. A 16-bit DAC over 10 V gives 0.153 mV per step, about 0.18 cents per step.

## 3. dsp.coffee DPT

| Claim | Label | Source |
|---|---|---|
| Built on an Electrosmith Daisy Patch Submodule; adds a 4-channel 12-bit SPI DAC **DAC7554**, scaled to -7 V to +7 V (BOM U2 DAC7554IDGS); native 2 x 12-bit CV out scaled to -5 V to +10 V; total 6 x 12-bit CV outs, no 16-bit output | OBSERVED | https://github.com/joemisra/dpt (README, BOM) ; https://dsp.coffee/products/product ; https://github.com/joemisra/dpt/blob/main/dpt-documentation.md (summary) |
| Other I/O: 8 pots, 8 CV in (pots become attenuators when jack patched), 2 gate in, 2 gate out, stereo audio in/out, TRS MIDI in/out (HCPL-0631 opto, A/B auto-sense), SD card, expander header (+5 V, +3V3, SPI, UART, I2C, USB) | OBSERVED | README; product page |
| Width: documentation page says Eurorack 3U, **20 HP**, about 35 mm deep with Patch SM installed. README and product page do not state HP | OBSERVED (single source, summary; doc marked work-in-progress with TBD items) | dpt-documentation.md |
| Network: no Ethernet or Wi-Fi implemented; docs mention only a planned "WiFi/Bluetooth connectivity option"; USB host for MIDI devices listed as planned | OBSERVED (summary) | dpt-documentation.md |
| Price $400.00 USD, status "Sold out"/pre-order, minimum batch of 5, "ETA depends on demand"; price rose for parts costs and tariffs; "very much developer oriented", firmware "under active development" | OBSERVED | https://dsp.coffee/products/product (2026-11-12) |
| Repo: 79 commits, 1 branch, no releases, last commit Jan 2, 2026 ("Update availability information in README.md"), C++ firmware against libDaisy v8 | OBSERVED | https://github.com/joemisra/dpt |
| Codec conflict (README PCM3080, product page WM8731) | OBSERVED (inconsistent) | see 2.3 |

## 4. Fit against Output Module targets (facts only, no decision)

| Target | Fact available | Gap |
|---|---|---|
| Transport-to-jack <= 2 ms p99 | USB poll 1 ms; observed end-to-end spreads 0.6-3 ms on desktop OSes via USB-MIDI | No p99 numbers for USB-MIDI to CV; none for iOS |
| Clock jitter <= 100 us RMS | UMP JR resolution 31.25 us; one RMS data point 0.038 ms for DAW-to-DIN clock | No measurement of USB-MIDI 2.0 JR playout on any host |
| >= 16-bit pitch DAC, >= 4 CV out | Patch SM: 2 x 12-bit; DPT: 6 x 12-bit | Requires external DAC either way (DPT's DAC7554 is also 12-bit) |
| Existing Ops lane (CBOR over serial) | iOS cannot open CDC without MFi/DriverKit | Choice of fallback transport for iOS is open |

## 5. Corrections to likely assumptions
- USB-MIDI 1.0 timestamps: none (INFERRED from class spec; TinyUSB doc shows 4-byte event packets).
- Patch SM CV outs are 0-5 V, not bipolar; DPT scales them to -5/+10 V with its own circuit (OBSERVED).
- The DPT README and product page disagree on the Patch SM codec.

## 6. Source access notes
- electro-smith.com/products/patch-sm returned 404 after redirecting to daisy.audio; electro-smith.com/daisy/patch-sm redirected to https://daisy.audio/products/patch-submodule, which worked.
- Mouser/DigiKey pages not read in full; LCSC pages were.

## 7. Could not verify
- USB-MIDI jitter on iOS/iPadOS; device-to-jack latency measurements; SysEx streaming throughput per OS.
- Whether any host emits JR timestamps on USB; TinyUSB MIDI2 maturity and release.
- iOS bus-power limit for class-compliant devices.
- RP2040 USB/timer/longevity statements (product page text gave no specs), STM32H7 USB/SPI/I2S counts from ST pages, H723VGT6 price, exact STM32 part inside the Patch SM, real PCM codec in the Patch SM, Embassy/Zephyr per-chip support levels.
- Qty-10 price for the Patch SM; DigiKey/Mouser tier tables.
- Wi-Fi cert cost, 6N138/H11L1 suitability, USB HS microframe and 1 ms FS frame statements (spec knowledge only).
