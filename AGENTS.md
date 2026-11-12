# AGENTS.md

Read [FACTS.md](FACTS.md) and [docs/handoff/NEXT.md](docs/handoff/NEXT.md) first.

## Checks

    python -m pytest beatoven/output_module
    python scripts/check_spec_trace.py
    python -m beatoven.output_module replay-check beatoven/output_module/vectors/stream.json

## Rules

- Do not edit existing public names or schemas. Propose changes as an ADR in `docs/adr/`.
- Hardware control is denied by default. Never add a way around the Hardware Lane Grant.
- Use the words in [GLOSSARY.md](GLOSSARY.md). The hardware is "the Output Module (PROPOSED)". Never write "Beatoven" for this project.
- Label claims OBSERVED, INFERRED or SPECULATIVE in specs and research. Never report a plan as a measurement.
- If `beatoven/output_module/vectors/` changes, say so: the hardware repository vendors it.
- Hand-offs go in `docs/handoff/NEXT.md`.
