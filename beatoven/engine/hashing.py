import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

FLOAT_PRECISION = 6


def _normalize(obj: Any) -> Any:
    if isinstance(obj, float):
        return round(obj, FLOAT_PRECISION)
    if isinstance(obj, dict):
        return {key: _normalize(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    return obj


def stable_json_dumps(obj: Any) -> str:
    normalized = _normalize(obj)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(stable_json_dumps(obj).encode("utf-8"))


def hash_pack(pack: dict) -> str:
    pack_copy = deepcopy(pack)
    provenance = pack_copy.get("provenance", {})
    provenance.pop("output_hashes", None)
    pack_copy["provenance"] = provenance
    return sha256_json(pack_copy)


def hash_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())
