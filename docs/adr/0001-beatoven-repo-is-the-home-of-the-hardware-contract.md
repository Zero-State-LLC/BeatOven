# 1. This repo is the home of the hardware contract

Status: ACCEPTED (operator instruction, 2026-11-11)

## Context

"What BeatOven sends to hardware" was described in three places: this repo (archived at the time), a placeholder overlay in Abraxas, and Notion canon. See `specs/001-output-module/audit.md` row 8.

## Decision

The Output Stream contract, its adapters, the host driver and the simulated device live in this repo under `beatoven/output_module/`. The physical Output Module lives in a separate hardware repo (working name Kiln), which vendors the contract and golden vectors at a named commit and never edits them.

Abraxas keeps its upstream emitters (`AudioControlFrame`, `BeatOvenOverlay`). Notion canon remains the authority on roles and permissions.

## Consequences

- A contract change is made here, then re-vendored into the hardware repo.
- The hardware repo's firmware must reproduce this repo's golden jack trace byte for byte.
