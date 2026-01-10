import argparse
import json
from pathlib import Path

from beatoven.engine.io import ensure_dir, write_json, write_text
from beatoven.engine.render import render_pack, render_report_bundle


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="BeatOven overlay renderer")
    parser.add_argument("render", nargs="?")
    parser.add_argument("--in", dest="input_path", required=True)
    parser.add_argument("--out", dest="output_dir", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--daw", default="GENERIC")
    parser.add_argument("--abx-gt", dest="abx_gt_path")

    args = parser.parse_args()

    oracle_path = Path(args.input_path)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    oracle_v2 = _load_json(oracle_path)
    overlays = {}
    if args.abx_gt_path:
        overlays["abx_gt"] = _load_json(Path(args.abx_gt_path))

    pack = render_pack(oracle_v2, overlays, seed=args.seed, daw=args.daw)
    bundle = render_report_bundle(pack)

    write_json(output_dir / "beatoven_midi_pack.v0.json", pack)
    if pack.get("cv"):
        write_json(output_dir / "beatoven_cv_pack.v0.json", pack["cv"])

    write_text(output_dir / "beatoven_session_recipe.v0.md", bundle["session_recipe_md"])
    write_json(output_dir / "provenance_manifest.v0.json", bundle["provenance_manifest"])
    write_json(output_dir / "determinism_report.v0.json", bundle["determinism_report"])


if __name__ == "__main__":
    main()
