# BeatOven Overlay v0.1

- Deterministic renderer: OracleSignalLayer.v2 -> BeatOvenPack.v0
- Local-only, no network.
- Produces: MIDI pack JSON + optional CV pack JSON + session recipe + provenance/determinism reports.

CLI:
- beatoven render --in oracle.json --out ./out --seed 1337 --daw ABLETON
