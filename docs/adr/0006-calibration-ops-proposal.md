# 6. Calibration commands on the Ops lane (proposal)

Status: PROPOSED. The existing Ops-lane kinds (`LOAD_PRESET`, `LOAD_KIT`, `COMMIT_PATTERN`, `STAGE_NEXT`, `PING`) are unchanged by this document.

## Context

Pitch accuracy of ±1 cent per octave needs per-channel calibration. The firmware core already stores a calibration record: 8 entries of gain in parts per million and offset in sixteenths of an LSB, with a CRC (Kiln `docs/firmware-architecture.md`). There is no way to drive a raw DAC code or write that record from the host: the reference device acknowledges only `PING` (spec, open clarification 5).

## Proposal

Three new Ops kinds, carried in the same CBOR map `{kind, nonce, payload}` and acknowledged with the same `{ack, ok}`:

| Kind | Payload | Effect |
|---|---|---|
| `CAL_RAW` | `{channel: wire id, code: 0..65535}` | Output this DAC code on one CV channel, bypassing calibration. |
| `CAL_WRITE` | `{entries: [{channel, gain_ppm, offset_lsb16}, ...]}` | Store the record. The device computes and stores the CRC. |
| `CAL_READ` | `{}` | Return the stored record in the acknowledgement. |

Rules:

1. Legal only in `SYNCED`. In `STREAMING` the device answers `ok: false` and changes nothing. No new lifecycle state.
2. `CAL_RAW` is hardware control, so the host requires a Hardware Lane Grant before sending it, as it does before playing.
3. A raw output is not a Safe Value. On `SYNC_TIMEOUT`, on any timing loss, or when a stream begins, CV outputs return to their Safe Value policy.
4. `CAL_WRITE` validates every entry against the Descriptor (channel exists and is a CV channel; gain and offset within stated bounds) and writes all or nothing.
5. Gates, clock and reset have no calibration and reject `CAL_RAW`.

## Migration

Additive. A device that does not know the kinds answers `ok: false`, which is what the reference device does for any unknown kind today. The Descriptor gains `calibration: true` where supported.

## Open

- `[NEEDS CLARIFICATION: bounds for gain_ppm and offset_lsb16]` The firmware's record fields set the storage width; the allowed range is not chosen.
- `[NEEDS CLARIFICATION: should CAL_WRITE need a second confirmation, since a bad record detunes every later stream?]`
- Nothing here is implemented in the reference device or the firmware.
