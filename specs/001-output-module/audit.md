# Audit: what blocks the Output Module

> This audit records the state found on 2026-11-11. The operator ruled on its open questions on 2026-11-12; see `docs/decisions/applied.md`. Rows below are kept as found, except where a resolution is noted.

Date: 2026-11-11. Repo state audited: `main@59312f5` (before this branch). Abraxas at `658fed92`.

Labels: **OBSERVED** means read in the cited source. **INFERRED** means reasoned, with the basis given. **SPECULATIVE** means a hypothesis.

"The Output Module" is a PROPOSED name. See the glossary delta.

## Top 10, ranked by how much each blocks the Output Module

| # | Problem | Evidence | Impact | Resolution |
|---|---|---|---|---|
| 1 | **Authority conflict.** Canon forbids hardware control; the Output Module is hardware control. | OBSERVED: `hardware_control_allowed: false` in [Spine 006](https://app.notion.com/p/3563e8ba2f5c81af8873d81fad20faa9) (System Identity, every contract's `authority` block, SEAL) and [Spine 009](https://app.notion.com/p/3563e8ba2f5c81f48969fd9763280c72) (same places; bridge authority `PLAN_ONLY_NO_RENDER_NO_HARDWARE`). OBSERVED: the Pack schema calls `cv` "no hardware IO" (`beatoven/schemas/beatoven.pack.v0.schema.json:113`). | Nothing may drive a jack until an operator grants a lane. | Code keeps the default at deny: a real transport needs an operator grant file (`beatoven/output_module/authority.py`). The operator asked on 2026-11-11 for the software and a hardware repo to be built; that is OBSERVED as a build instruction, and only INFERRED as intent to grant. Canon is unchanged. `[NEEDS CLARIFICATION: operator decision on hardware lane authority — amend Spine 006/009 or issue a scoped grant]` |
| 2 | **Four incompatible "to hardware" contracts.** | OBSERVED: see the comparison table below. | No device can implement "BeatOven output"; there is no single thing to implement. | One canonical contract, `beatoven.output_stream.v1`, with an adapter per existing contract. Built on this branch; migration table in `plan.md`. |
| 3 | **The `cv` block is not playable.** Unitless values from a seeded RNG, no voltage mapping, and both lanes share one list. | OBSERVED: `beatoven/engine/mapping.py:112-121`: `rng.random()` points; the same `points` list is assigned to the `CLOCK` and `MOD_CV` lanes; only those two lane types are emitted. OBSERVED: the schema allows `PITCH_CV`, `GATE`, `TRIGGER`, `RESET` (`beatoven.pack.v0.schema.json:122`) but nothing emits them. OBSERVED: `cv` is only emitted when `meme_velocity > 0.55` (`beatoven/engine/render.py:131-132`). | Pitch, gate, trigger and accent never reach `cv`. A clock lane of random numbers has no meaning. | The Pack adapter takes pitch and gates from `midi.tracks`, takes the clock from a rate, and reports the CLOCK lane points as `NOT_COMPUTABLE`. A Pack v1 that emits typed lanes is a proposal in `plan.md`, not an edit. |
| 4 | **Pack time has no unit, and its two clocks disagree.** | OBSERVED: `t` and `dur` are bare numbers in the schema (`beatoven.pack.v0.schema.json:63-64, 87, 104, 126`). OBSERVED: notes use `step * grid`, markers sit at 0, 8, 16, clips declare `bars` 4 or 8 (`mapping.py:55-58, 71, 77, 79`); beats and bars both fit. OBSERVED: `clock_hz = 2 + meme_velocity * 6` (`mapping.py:113`) is not derived from `tempo_bpm` (`mapping.py:26`). | A device cannot schedule an event whose time unit is unknown. Two unrelated clocks cannot both be right. | The adapter refuses to run without an explicit `time_unit`. Resolved 2026-11-12 by the operator: the unit is bars (OBSERVED in `mapping.py:90-93`; the earlier inference of beats was wrong), and the clock is derived from `tempo_bpm`; `cv.clock_hz` is not used. |
| 5 | **SEED determinism stops at the host.** No clock-sync model, no jitter budget, and `fail_closed_on_timing_loss` is a name with no definition. | OBSERVED: the term appears once, as a constraint on `RUNE.REALTIME_MIDI_STREAM` in [MIDI Batch 003](https://app.notion.com/p/3543e8ba2f5c8159ba9deba79b95df75), with no behaviour given. OBSERVED: no match for `fail_closed`, `clock_sync` or a jitter budget in the repo (grep on `main@59312f5`; "jitter" appears only as a video-shake feature). OBSERVED: `ResonanceFrame` ids and timestamps come from wall-clock time (`beatoven/dspcoffee_bridge/schema.py:101-102`), so two runs differ. | "Same inputs give byte-identical outputs" cannot be claimed at the jack. | The contract timestamps every event in microseconds; the device plays on its own clock after a sync exchange; timing loss has a defined effect (gates low, clock stopped, CV hold or slew to safe). Built and tested in simulation; the state machine is in `spec.md`. |
| 6 | **The Realtime lane assumes a network the DPT does not have, and its latency claim was never measured.** | OBSERVED: the bridge sends UDP to an IP address (`beatoven/dspcoffee_bridge/transport_udp.py:22-33`; example `192.168.1.50:9000` at `README_SNIPPET.md:20`). OBSERVED: the DPT lists TRS MIDI, SD and USB on an expander header, with Wi-Fi only under "Planned Features" (`research/prior-art.md`, section "DPT I/O"). INFERRED from that list: no UDP endpoint exists. OBSERVED: `README.md:103` states "Latency: <1ms"; no measurement, test or method exists in the repo. OBSERVED: `/macro` and `/meta` records carry no timestamp (`transport_udp.py:28, 32`). | Lane A has no receiver, and nothing it sends could be scheduled. | Treat "<1ms" as SPECULATIVE. The canonical contract replaces Lane A for the Output Module. The record formats stay untouched for any future DPT work. |
| 7 | **The firmware counterpart was never written.** | OBSERVED: `beatoven/dspcoffee_bridge/README_SNIPPET.md:59-67` lists the firmware as "Next steps". OBSERVED: no C or C++ source in the repo (`git ls-files`). OBSERVED: `_metrics_to_macros` says "You will tune this once your dsp.coffee macro table exists" (`runtime.py:17`). | The bridge has never talked to a device. Every claim about it is untested. | Firmware lives in the separate hardware repo and is tested against golden vectors exported from this repo (`beatoven/output_module/vectors/`). |
| 8 | **No home for the work.** | OBSERVED: this repo was archived until 2026-11-11. OBSERVED: Abraxas holds a placeholder overlay ("Deterministic sonification mapping placeholder", `Abraxas/abraxas/overlays/beatoven.py:17`). OBSERVED: the six schemas and file tree in Spine 006 exist only in Notion; none of those paths are in either repo. OBSERVED: `pyproject.toml:7` says version 0.1.0 and `setup.py:12` says 1.0.0. | Three places each look authoritative. | Decided by the operator on 2026-11-11: software lives in this repo (now unarchived); hardware lives in a second repo. ADR candidate: "BeatOven repo is the home of the hardware contract; Abraxas keeps only the upstream emitters." |
| 9 | **Canon names schemas it never defines.** | OBSERVED: `BeatOvenRun.v1` is named as an output in the [Full Stack page](https://app.notion.com/p/3543e8ba2f5c81e5ba15e0c103de102d) but has no schema. OBSERVED: `MIDIEventStream.v1` has `"events": []` with no item shape, and `MIDIClipIR.v1` has `"tracks": []` ([MIDI Batch 003](https://app.notion.com/p/3543e8ba2f5c8159ba9deba79b95df75), Full Stack page). OBSERVED: `OraclePacket.v1` is named, not defined. OBSERVED: the code's input is `oracle_signal_layer.v2` with `vector_mix` and `kairos` (`render.py:20-22`), not the nine Oracle features of `OracleToMusicPacket.v1`. | An adapter for `MIDIEventStream.v1` has to invent the event shape. "Send the same BeatOvenRun.v1 twice" has no object to send. | The adapter reads a PROPOSED event shape, flagged in `plan.md`. `[NEEDS CLARIFICATION: MIDIEventStream.v1 event item shape]` `[NEEDS CLARIFICATION: BeatOvenRun.v1 schema]` |
| 10 | **No NVIDIA-first decision record, and the repo does not test clean.** | OBSERVED: the CLIP provider picks `cuda` when available and loads `openai/clip-vit-base-patch32` (`beatoven/media_intel/providers/clip_provider.py:34-35`); no decision record exists. OBSERVED: the "motif training run" is named in the [Fold-In Seal](https://app.notion.com/p/3543e8ba2f5c81b49c1bd224aa844d99) and has no code in the repo (the only `motif` match is a marker label in `mapping.py`). OBSERVED on this machine, Python 3.14.7: on `main`, `pytest --ignore=beatoven/media_intel` reports failures in `beatoven/tests/test_api.py` and `test_doctrine.py` (HTTP 500), and `media_intel` tests fail to import without `cv2`. | ML layers have no recorded platform choice. A red baseline hides regressions. | `research/nvidia-decision.md` records the choice per layer. The baseline failures are pre-existing and out of scope here; listed in `docs/handoff/NEXT.md`. |

### The eight known problems: confirmed or refuted

| Known item | Verdict | Row |
|---|---|---|
| 1. Authority conflict | Confirmed | 1 |
| 2. No home for the work | Confirmed; resolved by operator decision | 8 |
| 3. Four incompatible contracts | Confirmed | 2 |
| 4. `cv` is unitless RNG output | Confirmed, and worse: both lanes share one list | 3 |
| 5. Realtime lane assumes UDP the DPT lacks; "<1ms" unmeasured | Confirmed | 6 |
| 6. SEED stops at the host | Confirmed | 5 |
| 7. Firmware never written | Confirmed | 7 |
| 8. No NVIDIA-first record | Confirmed | 10 |

Added by this audit: row 4 (time unit and clock disagreement) and row 9 (undefined canon schemas).

## Comparison of the four contracts (item 3)

| Field | Pack `cv` (+ `midi`) | `ResonanceFrame` / Realtime lane | `AudioControlFrame` / `cv_gate_map` | `MIDIEventStream.v1` |
|---|---|---|---|---|
| Defined in | `beatoven/schemas/beatoven.pack.v0.schema.json:111-132`; emitted by `mapping.py:111-121` | `dspcoffee_bridge/schema.py:18-105`; `transport_udp.py:26-33` | `Abraxas/abraxas/sonification/schema.py:10-18`; `Abraxas/abraxas/overlays/beatoven.py:32-35` | Notion MIDI Batch 003 |
| Status | Runs | Runs on the host; no receiver exists | `AudioControlFrame` runs; `cv_gate_map` is a placeholder | Canon only; no code |
| Time base | `t`, unit undefined | `ts_ms` wall clock on the frame; none on the wire records | `window_utc` identifier; no duration | `sync_mode`: `delta_time`, `absolute_tick` or `wall_clock`; no resolution given |
| Tempo / clock | `midi.tempo_bpm` 40–220 and a separate `cv.clock_hz` 0.1–30 | `RhythmTokens.bpm`; `/meta bpm` | `tempo_bpm` 40–160; `cv_gate_map.clock_hz = tempo / 60` | Not defined |
| Pitch | MIDI note 0–127 in `midi.tracks` only; `PITCH_CV` lane allowed, never emitted | None | None (`scale`, `chords` as names) | Not defined (events empty) |
| Gate / trigger | Note `t` + `dur` in `midi` only; `GATE` and `TRIGGER` lanes allowed, never emitted | Step grids `kick`, `snare`, `hat`, `perc`, values 0–1 "probability/velocity" | `gate_pattern` string of `0`/`1`; step length undefined | Not defined |
| Modulation | `MOD_CV` points 0–1, unitless; `cc_lanes` 0–127 | Eight metrics 0–1; `/macro <preset> <name> <value>` | Five fields 0–1 | Not defined |
| Reset | `RESET` lane allowed, never emitted | None | None | Not defined |
| Voltage mapping | None | None | None | None |
| Transport | None ("no hardware IO") | UDP text (Lane A), serial CBOR with ACK (Lane B) | None | `transport.target`: `DAW`, `hardware_synth`, `virtual_instrument`, `OSC_bridge` |
| Delivery guarantee | n/a | Lane A none; Lane B nonce ACK, 3 retries | n/a | `command_rate_budget`, no unit |
| Timing-loss behaviour | None | None | None | `fail_closed_on_timing_loss`, undefined |
| Determinism | Seeded; hashes in `provenance` | `provenance_hash`; id and `ts_ms` from wall clock unless supplied | Deterministic mapping, `provenance` dict | `stream_id` as `sha256:<oracle_stream>` |
| Authority field | None | None | None | None |

All four lack a voltage mapping and a defined timing-loss behaviour. Three of four lack pitch. None can be handed to a device as it stands.

## Gate 0

- `audit.md` exists: this file.
- Every row is cited: yes, by `file:line` or Notion URL.
- Comparison table filled in: yes.
