from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import json

def validate_dir(jsonld_dir: Path) -> List[Tuple[Path, str]]:
    try:
        from openminds import Collection
    except Exception as e:
        return [(jsonld_dir, f"openMINDS validation unavailable: {e}")]

    coll = Collection()
    errors: List[Tuple[Path, str]] = []

    for fp in sorted(jsonld_dir.glob("*.jsonld")):
        try:
            payload = json.loads(fp.read_text())
            coll.add(payload)
        except Exception as e:
            errors.append((fp, f"Unreadable JSON-LD: {e}"))

    failures = coll.validate()
    for f in (failures or []):
        try:
            path_hint = getattr(getattr(f, "node", None), "id", None) or getattr(f, "node", None)
            msg = getattr(f, "message", None) or str(f)
            errors.append((Path(str(path_hint) or "unknown"), msg))
        except Exception:
            errors.append((jsonld_dir, str(f)))

    return errors
