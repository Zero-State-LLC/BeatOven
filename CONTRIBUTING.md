# Contributing

## Before you start

1. Read [FACTS.md](FACTS.md) and [docs/handoff/NEXT.md](docs/handoff/NEXT.md).
2. Use the words in [GLOSSARY.md](GLOSSARY.md).
3. Check the [project board](https://github.com/orgs/Zero-State-LLC/projects/33) for an existing item. It is private to the organization.

## Set up

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,hardware]"
```

## Checks to run before a pull request

```bash
python -m pytest beatoven/output_module
python scripts/check_spec_trace.py
python -m beatoven.output_module replay-check beatoven/output_module/vectors/stream.json
```

The wider suite is `python -m pytest`. It needs `opencv-python-headless` for the media intelligence tests. One test there, `test_infer_era_unknown`, is known to fail.

## Rules that reviewers hold you to

- **Determinism.** No wall-clock time or unseeded randomness in anything that reaches an output.
- **Fail closed.** Malformed input ends in an error or a safe state, never a guess.
- **Public shapes change by proposal.** `render_pack`, the Pack schema, the bridge types, the Ops lane kinds and the Output Stream contract change only through an ADR in `docs/adr/` with a migration and a version bump.
- **Hardware control stays off by default.** Do not add a path that drives a device without a Hardware Lane Grant.
- **Claims need proof.** "Passing" or "measured" needs the output that shows it. A plan is labelled a plan.
- **Spec chain.** A new capability traces Journey, Workflow, State Transition, Contract, Acceptance Test, Task. `scripts/check_spec_trace.py` enforces the last three links.

## Branches and commits

- Branch from `main`: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- One logical change per pull request. Say what you verified and what you did not.
- Delete your branch after it merges.

## Versioning and releases

- The package follows Semantic Versioning. The single source is `__version__` in `beatoven/__init__.py`.
- Schema identifiers (`beatoven.output_stream.v1`) have their own version in their name. A breaking change to a schema is a new identifier, not an edit.
- To release: update `CHANGELOG.md`, bump `__version__`, merge, then tag `vX.Y.Z` on `main` and publish a GitHub release with the changelog section.
- If the golden vectors in `beatoven/output_module/vectors/` change, the hardware repository must re-vendor them.
