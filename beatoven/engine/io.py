import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False)


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
