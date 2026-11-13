# 6. Calibration commands on the Ops Lane

Status: ACCEPTED by the operator on 2026-11-13, as amended below. Implemented in the reference device and the host driver. The existing Ops Lane kinds (`LOAD_PRESET`, `LOAD_KIT`, `COMMIT_PATTERN`, `STAGE_NEXT`, `PING`) are unchanged.

## Context

Pitch accuracy of ±1 cent per octave needs per-channel calibration. The firmware core stores a calibration record: 8 entries of gain in parts per million and offset in sixteenths of an LSB, with a CRC (Kiln `docs/firmware-architecture.md`). There was no way to write that record from the host: the reference device acknowledged only `PING` (spec, former open clarification 5).

## Decision

Three new Ops kinds, carried in the same CBOR map `{kind, nonce, payload}`. The acknowledgement is the same `{ack, ok}`, with an added `payload` where a kind returns data.

| Kind | Payload | Effect |
|---|---|---|
| `CAL_READ` | `{}` | Returns `{state, entries}`: `state` is `identity` or `stored`, and `entries` lists every CV channel. |
| `CAL_WRITE` | `{entries: [{channel: wire id, gain_ppm, offset_lsb16}, ...]}` | Stores the record. Channels not named are left uncorrected. The record it replaces is kept. |
| `CAL_REVERT` | `{}` | Swaps back to the record the last write replaced. Refused if there is none. |

Rules:

1. Legal only in `SYNCED`. In any other state the device answers `ok: false` and changes nothing. No new lifecycle state.
2. None of the three moves a jack. Calibration changes the code sent to the DAC for a requested voltage; the Output Stream, the played hash and the Jack Trace are unchanged by it.
3. `CAL_WRITE` validates every entry and writes all or nothing: the channel exists on this device and is a pitch or mod CV channel, no channel appears twice, and the values are integers within the bounds below.
4. Bounds: gain within ±20,000 ppm, offset within ±1,600 sixteenths of an LSB (±100 LSB, about ±15 mV on a 10 V, 16-bit channel). INFERRED from 0.1 % resistors and the DAC's stated errors; a value outside them is treated as a mistake or a fault. **These are a proposal until a board has been measured.**
5. All 8 CV channels may be calibrated. Only the pitch channels are required by the bench procedure.
6. The device keeps exactly one previous record. If both the current and the previous record fail their check, the device uses identity (no correction) and reports `identity`. It still plays.
7. The Descriptor gains the optional field `calibration`, `"identity"` or `"stored"`, where the device supports these commands. The field stays under `beatoven.output_module_descriptor.v1`; absent means unsupported. No Descriptor version bump.

### Authority

- `CAL_WRITE` and `CAL_REVERT` on real hardware need a Hardware Lane Grant that names the scope `output_module.calibrate`. That scope is separate from `output_module`: a grant to play does not permit changing calibration, and a grant to calibrate does not by itself open play.
- A grant naming `output_module.calibrate` is invalid unless it states `expires_at`.
- `CAL_READ` needs no calibration scope.
- The grant is checked by the BeatOven host driver before it sends anything. The device does not verify a grant. This is a known limit: the Hardware Lane binds Zero State's software and agents, not the device.

### Rejected: `CAL_RAW`

The proposal had a fourth kind that output a raw DAC code with calibration bypassed. It is dropped. Writing an identity record and playing an ordinary Output Stream of known voltages does the same job through the validated stream path, so no command produces a voltage outside that path.

## Calibration procedure this implies

1. `CAL_WRITE` an identity record (every entry 0, 0).
2. Play an Output Stream that steps each pitch channel through known voltages; measure each at the jack.
3. Compute gain and offset per channel (the firmware core's two-point solve does this).
4. `CAL_WRITE` the result, then replay the stream to confirm. `CAL_REVERT` if it is worse.

## Migration

Additive. A device that does not know the kinds answers `ok: false`, as the reference device does for any unknown kind. A Descriptor without the field still parses (acceptance test AT-034). The golden vectors do not change: the reference device starts at identity, and calibration does not alter the Jack Trace.

Kiln's firmware core must add the three kinds and the previous-record slot, and regenerate its Descriptor test fixture.

## Consequences

- The reference device's arithmetic for the corrected code is the firmware core's (`kc_calib_apply`), so the two can be compared code for code.
- The firmware's own solve accepts up to ±100,000 ppm and ±4,096 LSB. `CAL_WRITE` is stricter; a board that needs more than the bounds here fails calibration and is investigated.
