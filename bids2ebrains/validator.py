from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import json

from .scanner import Scanner
from .utils import local_name

_LAST_VALIDATION_MODE = "unknown"
def get_last_validation_mode() -> str:
    return _LAST_VALIDATION_MODE


def _minimal_validate_file(fp: Path) -> List[Tuple[Path, str]]:
    """Schema-light validation that never crashes and gives actionable messages."""
    errs: List[Tuple[Path, str]] = []
    try:
        payload = json.loads(fp.read_text())
    except Exception as e:
        errs.append((fp, f"Unreadable JSON-LD: {e}"))
        return errs

    if not isinstance(payload, dict):
        errs.append((fp, "Top-level JSON-LD must be a JSON object"))
        return errs

    missing_core = [k for k in ("@id", "@type") if k not in payload]
    if missing_core:
        errs.append((fp, f"Missing {', '.join(missing_core)}"))
        return errs

    typ = payload.get("@type")
    if isinstance(typ, list) and typ:
        typ = typ[-1]
    if isinstance(typ, str):
        tname = local_name(typ)
    else:
        tname = None
    if not tname:
        errs.append((fp, "Unrecognized @type"))
        return errs

    required = Scanner.MANDATORY.get(tname, [])
    for key in required:
        if key not in payload or payload[key] in ("", [], None):
            errs.append((fp, f"Missing mandatory field: {tname}.{key}"))

    return errs


def validate_dir(jsonld_dir: Path) -> List[Tuple[Path, str]]:
    global _LAST_VALIDATION_MODE
    _LAST_VALIDATION_MODE = "unknown"

    files = sorted(jsonld_dir.glob("*.jsonld"))
    errors: List[Tuple[Path, str]] = []

    try:
        from openminds import Collection 
        coll = Collection()

        adders = [getattr(coll, name, None) for name in ("add_jsonld", "add_from_jsonld", "add")]
        adders = [a for a in adders if callable(a)]

        ingested = 0
        failed_files: List[Path] = []

        for fp in files:
            try:
                payload = json.loads(fp.read_text())
            except Exception as e:
                errors.append((fp, f"Unreadable JSON-LD: {e}"))
                continue

            added = False
            for adder in adders:
                try:
                    adder(payload) 
                    added = True
                    ingested += 1
                    break
                except Exception:
                    continue

            if not added:
                failed_files.append(fp)

        if ingested:
            _LAST_VALIDATION_MODE = "full-openMINDS"
            try:
                failures = coll.validate() or []
                for f in failures:
                    node = getattr(f, "node", None)
                    msg = getattr(f, "message", None) or str(f)
                    hint = None
                    if isinstance(node, (str, Path)):
                        hint = str(node)
                    else:
                        hint = getattr(node, "id", None) or getattr(node, "uuid", None) or ""
                    errors.append((Path(hint or "unknown"), msg))
            except Exception:
                failed_files = files
                _LAST_VALIDATION_MODE = "basic-fallback"
        else:
            _LAST_VALIDATION_MODE = "basic-fallback"

        for fp in failed_files:
            errors.extend(_minimal_validate_file(fp))

        return errors

    except Exception:
        _LAST_VALIDATION_MODE = "basic-fallback"
        for fp in files:
            errors.extend(_minimal_validate_file(fp))
        return errors
