from __future__ import annotations
import hashlib
from typing import Tuple
import re

def sha256_and_size(path: str) -> Tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            size += len(chunk)
            h.update(chunk)
    return h.hexdigest(), size

def local_name(uri: str) -> str:
    return uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]

def is_iri(s: str) -> bool:
    return isinstance(s, str) and bool(re.match(r"^https?://", s))

