from __future__ import annotations
import os

def _detect_openminds_namespaces():
    try:
        try: # prefer values from openMINDS_Python (if available)
            from openminds.v3.core.data.license import License
        except Exception:
            from openminds.core.data.license import License 

        ctx = getattr(License, "context", {}) or {}
        vocab = ctx.get("@vocab") or "https://openminds.ebrains.eu/vocab/"

        type_uri = getattr(License, "type_", "https://openminds.ebrains.eu/core/License")
        core_base = type_uri.rsplit("/", 1)[0] + "/"

        return vocab, core_base
    except Exception:
        return (
            "https://openminds.ebrains.eu/vocab/",
            "https://openminds.ebrains.eu/core/",
        )

OM_VOCAB, OM_CORE = _detect_openminds_namespaces()

KG_BASE = os.getenv("EBRAINS_KG_BASE", "https://core.kg.ebrains.eu/v3/instances")
