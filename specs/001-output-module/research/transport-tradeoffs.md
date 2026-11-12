# Transport trade-offs

Facts and their sources are in [transport-facts.md](transport-facts.md); section numbers below (§) point into it. Labels: OBSERVED, INFERRED, SPECULATIVE.

## The finding that drives the choice

No candidate transport delivers events to the device with timing good enough to play on arrival.

- USB full speed is polled once per 1 ms, giving roughly ±0.5 ms to ±1 ms of arrival jitter (OBSERVED, vendor forum statement, §1.2). A bench test of USB MIDI interfaces measured a 0.61 ms spread on macOS and 1.04–1.41 ms on Linux (OBSERVED, §1.2).
- The target is clock jitter ≤ 100 µs RMS. Arrival jitter of 0.6–1.4 ms cannot meet it (INFERRED from the two figures above).
- USB-MIDI 1.0 carries no timestamp on the wire (INFERRED from the spec's packet format, §1.3).

So the timestamp travels in the payload and the device schedules each event on its own clock. Once that is true, link jitter only has to be smaller than the look-ahead, and the transport choice turns on host support and cost.

## Comparison

| Transport | Latency / jitter | Host support (macOS, Linux, iOS) | Determinism | Cost / BOM risk | Ops lane survives? |
|---|---|---|---|---|---|
| **USB-MIDI 1.0, class compliant** | 1 ms polling; 0.61–1.41 ms measured spread (OBSERVED, §1.2). Absorbed by look-ahead scheduling (INFERRED). | All three without a driver (OBSERVED for CoreMIDI and ALSA, §1.5). iOS requires class compliance (OBSERVED, §1.5). | Good with payload timestamps; play-on-arrival is not deterministic (INFERRED). | No extra part: the MCU's USB device port (OBSERVED for RP2350, §2.1). | Yes, as data: the same CBOR map in a SysEx envelope. The u32 length prefix is replaced. |
| USB-MIDI 2.0 / UMP | JR Timestamps: 16-bit, 31.25 µs ticks, wraps at 2.048 s (OBSERVED tick, INFERRED wrap, §1.3). | CoreMIDI and ALSA ≥ 6.5 support UMP; some distro kernels ship it disabled (OBSERVED, §1.5). No evidence that any host emits JR timestamps over USB (not verified, §7). | Good in principle; unproven in practice. | TinyUSB has a MIDI 2.0 device driver; maturity not verified (§1.7, §7). | Yes, as UMP SysEx. |
| TRS MIDI, 31.25 kbaud | 320 µs per byte; about 1040 three-byte messages per second (INFERRED, arithmetic, §1.4). | Any MIDI interface. One-way on an input-only jack. | Good with payload timestamps, at a low event rate. | One optocoupler and a jack. | Only one-way: no ACK without a MIDI out. |
| I2C (Teletype ii) | No published timing data (OBSERVED absence, §1.8). | None: it is a module-to-module bus with a single leader (OBSERVED, §1.8). | Unknown. | Header only. | No. |
| UART / USB-CDC + CBOR (existing Ops lane) | Same USB polling as above (INFERRED). | macOS and Linux yes. iOS exposes no generic USB serial to apps without MFi or entitlements (OBSERVED via forum threads, not read in full, §1.5, §1.9). | Good with payload timestamps. | No extra part. | Yes, unchanged. |
| Wi-Fi + OSC | 1–5 ms jitter typical, tens of ms in other studies (OBSERVED via search summaries, papers not opened, §1.9). | All three. | Poor: jitter exceeds any reasonable look-ahead on a busy network (INFERRED). | Radio module, antenna, RF certification (cost not verified, §7). | Could, but nothing else recommends it. |

## Decision

**Primary: USB-MIDI 1.0, class compliant, with the Output Stream carried in System Exclusive.**

1. It is the only wired option that works on macOS, Linux and iOS without a driver or an entitlement.
2. Timing does not depend on it: the device schedules timestamped events, so the 1 ms polling grid is absorbed by a 50 ms look-ahead (INFERRED; proven only in simulation, see the test plan).
3. It needs no part beyond the MCU.
4. A DAW can still send plain notes and clock to the same port. That play-on-arrival mode is not SEED-deterministic and must be labelled so.

**Fallback: TRS MIDI in (Type A), same bytes.** It needs no computer USB port and no ground connection to the host. It is one-way, so there is no status or played-hash feedback, and the event rate is limited to about 195 Output Events per second (INFERRED: 3125 bytes per second ÷ 16 wire bytes per event). Fail-closed still works because the device enforces it.

**Rejected:**
- MIDI 2.0 JR Timestamps as the primary: no verified host that sends them over USB, 2.048 s wrap needs extra bookkeeping, and the device stack is unproven. Revisit when a host is verified.
- Wi-Fi/OSC: jitter and certification.
- I2C ii: not a host transport.
- USB-CDC serial as the primary: no iOS path.

## The Ops lane

Kept as a message kind, with its framing changed. The body is the same CBOR map `{kind, nonce, payload}` and the reply is the same `{ack, ok}`. The `[u32 length]` prefix is replaced by the SysEx envelope, 7-bit packing and a CRC-16, because MIDI data bytes cannot have bit 7 set and SysEx already delimits the message. The kind literals (`LOAD_PRESET`, `LOAD_KIT`, `COMMIT_PATTERN`, `STAGE_NEXT`, `PING`) are unchanged. `SerialOpsLane` and the u32 framing stay as they are for any DPT work.

The Realtime lane (`/macro`, `/meta` text records) is not carried to the Output Module. Its records have no timestamp, so they cannot be scheduled. The same information reaches the device as `SET_UV` and `CLOCK_PERIOD` events.

## Open items that could change this choice

- Decided 2026-11-12: iOS is not a required host for v1. USB-CDC is therefore viable, though nothing argues for switching.
- `[NEEDS CLARIFICATION: MIDI manufacturer ID]` The wire uses 0x7D, the non-commercial ID. A product needs an assigned ID.
- Not verified: sustained SysEx throughput per OS (§1.6, §7). A Windows update is reported to split SysEx (OBSERVED, anecdotal, §1.6). Windows is not a target host; if it becomes one, test first.

None of these blocks the transport choice.
