#!/usr/bin/env python3
"""Traceability check for a spec folder. Stand-in for spec-lint, which is not in this repo.

Checks: required files and sections exist; every FR names an acceptance test;
every AT named in the spec exists as a test function; every FR is named by a
task; the transitions table in spec.md equals the one in plan.md and in code.
Exit 0 only if all pass.
"""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec_dir = root / (sys.argv[1] if len(sys.argv) > 1 else "specs/001-output-module")
errors = []


def need(cond, msg):
    if not cond:
        errors.append(msg)


files = {n: spec_dir / n for n in ("spec.md", "plan.md", "tasks.md", "checklists/requirements.md")}
for n, p in files.items():
    need(p.exists(), f"missing {n}")
if errors:
    print("\n".join(errors)); sys.exit(1)
spec, plan, tasks = (files[n].read_text() for n in ("spec.md", "plan.md", "tasks.md"))

for section in ("## User stories", "## Functional requirements", "## Success criteria", "## Domain entities",
                "## Stateful behavior", "### Transitions", "### Illegal transitions", "stateDiagram-v2",
                "## Workflows", "## Traceability", "## Open clarifications"):
    need(section in spec, f"spec.md lacks {section!r}")
for section in ("## Stateful behavior", "## Workflows", "## Migration table", "## Canonical hardware contract"):
    need(section in plan, f"plan.md lacks {section!r}")
for wf in ("anti-slop-code", "production-systems", "google-developer-style"):
    need(wf in spec and wf in plan, f"workflow {wf} not named in spec and plan")
for owner in ("FORGE", "cloud agent", "SCRIBE", "ADVERSARY"):
    need(owner in spec, f"owner {owner} not named")

fr_rows = re.findall(r"^\| (FR-\d{3}) \|.*\| ([^|]+) \|$", spec, re.M)
frs = [fr for fr, _ in fr_rows]
need(len(frs) >= 1 and len(frs) == len(set(frs)), "FR ids missing or duplicated")
tests_src = "\n".join(p.read_text() for p in (root / "beatoven/output_module/tests").glob("test_*.py"))
test_ids = set(re.findall(r"def test_at(\d{3})_", tests_src))
for fr, acc in fr_rows:
    ids = re.findall(r"(AT|HT)-(\d+)", acc)
    need(ids, f"{fr} has no acceptance test")
    for kind, num in ids:
        if kind == "AT":
            need(num in test_ids, f"{fr} cites AT-{num}, which is not a test function")
    need(re.search(rf"{fr}\b", tasks), f"{fr} is not named by any task")
for num in set(re.findall(r"AT-(\d{3})", spec)):
    need(num in test_ids, f"spec cites AT-{num}, which is not a test function")
for num in test_ids:
    need(f"AT-{num}" in spec or re.search(rf"AT-\d{{3}}[–-]\d*", spec), f"test AT-{num} is not cited in the spec")
for line in re.findall(r"^- \[[ x]\] (001-T\d+) (.*)$", tasks, re.M):
    tid, body = line
    if re.search(r"FR-\d{3}", body):
        need("workflows:" in body, f"{tid} implements an FR but names no workflow")


def table(text):
    block = text.split("| from | event | guard | to | effect |", 1)[1]
    rows = []
    for ln in block.splitlines()[2:]:
        if not ln.startswith("|"):
            break
        rows.append(tuple(c.strip().strip("`") for c in ln.strip("|").split("|")))
    return sorted(rows)


sys.path.insert(0, str(root))
from beatoven.output_module import lifecycle as lc  # noqa: E402

code = sorted((r["from"], r["event"], r["guard"].replace("safe value", "Safe Value").replace("hardware lane", "Hardware Lane"),
               r["to"], r["effect"]) for r in lc.as_table())
need(table(spec) == table(plan), "transitions table differs between spec.md and plan.md")
need(table(spec) == code, "transitions table differs between spec.md and lifecycle.py")
need(len(lc.illegal_transitions()) == 40 and "40" in spec, "illegal transition count is not 40")
need(len(re.findall(r"\[NEEDS CLARIFICATION", spec)) >= 1, "no clarification markers")

if errors:
    print(f"FAIL ({len(errors)})"); print("\n".join(f"  - {e}" for e in errors)); sys.exit(1)
print(f"OK: {len(frs)} FRs, {len(test_ids)} acceptance tests, {len(code)} transitions, "
      f"{len(re.findall(r'NEEDS CLARIFICATION', spec))} clarification markers, 0 orphans")
