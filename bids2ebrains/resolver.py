from __future__ import annotations

from typing import Optional
from difflib import SequenceMatcher
import unicodedata

SIMILARITY_THRESHOLD = 0.60  


def _strip_accents(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _best_iri_from_person_obj(p, host: str = "kg.ebrains.eu") -> Optional[str]:
    for attr in ("iri", "uri"):
        v = getattr(p, attr, None)
        if isinstance(v, str) and v.startswith("http"):
            return v

    for attr in ("id", "uuid"):
        v = getattr(p, attr, None)
        if isinstance(v, str) and v:
            return f"https://{host}/api/instances/{v}"

    return None


def resolve_person_iri(
    first: Optional[str],
    last: Optional[str],
    orcid: Optional[str] = None,
    *,
    token: Optional[str] = None,
    host: str = "core.kg.ebrains.eu",
    scope: str = "released",
) -> Optional[str]:
    try:
        from fairgraph import KGClient
        import fairgraph.openminds.core as omcore

        omcore.set_error_handling(None)
        client = KGClient(host=host, token=token)

        if orcid:
            norm = str(orcid).strip()
            if norm and not norm.startswith("http"):
                norm = f"https://orcid.org/{norm}"

            try:
                matches = omcore.Person.list(client, size=25, scope=scope, orcid=norm)
                if matches:
                    iri = _best_iri_from_person_obj(matches[0], host="kg.ebrains.eu")
                    if iri:
                        return iri
            except Exception:
                pass

        if not last:
            return None

        candidates = []
        try:
            candidates = omcore.Person.list(client, size=500, scope=scope, family_name=last)
        except Exception:
            return None

        if not candidates:
            return None

        first_norm = _strip_accents(first or "").lower()
        best = None
        best_score = 0.0

        for p in candidates:
            gn = getattr(p, "given_name", None) or getattr(p, "first_name", None) or ""
            score = SequenceMatcher(None, _strip_accents(gn).lower(), first_norm).ratio()
            if score > best_score:
                best = p
                best_score = score

        if best is not None and best_score >= SIMILARITY_THRESHOLD:
            iri = _best_iri_from_person_obj(best, host="kg.ebrains.eu")
            if iri:
                return iri

    except Exception:
        return None

    return None
