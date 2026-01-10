from typing import Callable, List, Tuple

from beatoven.engine.hashing import sha256_json


def run_n_times(pack_fn: Callable[[], dict], n: int = 12) -> Tuple[List[str], bool]:
    hashes = []
    for _ in range(n):
        pack = pack_fn()
        hashes.append(sha256_json(pack))
    invariance = all(hash_value == hashes[0] for hash_value in hashes)
    return hashes, invariance
