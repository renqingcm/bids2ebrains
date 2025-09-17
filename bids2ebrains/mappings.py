from typing import Optional, Dict

def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def _build_maps() -> Dict[str, Dict[str, str]]:
    try:
        try:
            from openminds.v3.core.data.license import License
            from openminds.v3.core.data.product_accessibility import ProductAccessibility
            from openminds.v3.core.data.age_category import AgeCategory
        except Exception:
            from openminds.core.data.license import License               
            from openminds.core.data.product_accessibility import ProductAccessibility 
            from openminds.core.data.age_category import AgeCategory   

        def _collect(items, extra_names=None):
            m: Dict[str, str] = {}
            for obj in items:
                iri = getattr(obj, "id", None)
                if not iri:
                    continue
                candidates = []
                for attr in ("short_name", "full_name", "name"):
                    val = getattr(obj, attr, None)
                    if isinstance(val, str) and val:
                        candidates.append(val)
                if extra_names:
                    candidates.extend(extra_names(obj))
                for c in candidates:
                    m[_norm(c)] = iri
            return m

        license_map        = _collect(License.instances())
        accessibility_map  = _collect(ProductAccessibility.instances())
        age_category_map   = _collect(AgeCategory.instances())

        return {
            "license":        license_map,
            "accessibility":  accessibility_map,
            "age_category":   age_category_map,
        }
    except Exception:
        LICENSE = {
            "ccb y40": "https://openminds.ebrains.eu/instances/licenses/CC-BY-4.0",
            "ccby40":  "https://openminds.ebrains.eu/instances/licenses/CC-BY-4.0",
            "cc01 0":  "https://openminds.ebrains.eu/instances/licenses/CC0-1.0",
            "cc010":   "https://openminds.ebrains.eu/instances/licenses/CC0-1.0",
            "mit":     "https://openminds.ebrains.eu/instances/licenses/MIT",
            "apache20":"https://openminds.ebrains.eu/instances/licenses/Apache-2.0",
        }
        ACCESSIBILITY = {
            "freeaccess":       "https://openminds.ebrains.eu/instances/productAccessibility/freeAccess",
            "embargoedaccess":  "https://openminds.ebrains.eu/instances/productAccessibility/embargoedAccess",
            "controlledaccess": "https://openminds.ebrains.eu/instances/productAccessibility/controlledAccess",
        }
        AGE_CATEGORY = {
            "adult":       "https://openminds.ebrains.eu/instances/ageCategory/adult",
            "youngadult":  "https://openminds.ebrains.eu/instances/ageCategory/youngAdult",
            "primeadult":  "https://openminds.ebrains.eu/instances/ageCategory/primeAdult",
            "lateadult":   "https://openminds.ebrains.eu/instances/ageCategory/lateAdult",
            "adolescent":  "https://openminds.ebrains.eu/instances/ageCategory/adolescent",
            "juvenile":    "https://openminds.ebrains.eu/instances/ageCategory/juvenile",
            "infant":      "https://openminds.ebrains.eu/instances/ageCategory/infant",
            "neonate":     "https://openminds.ebrains.eu/instances/ageCategory/neonate",
            "perinatal":   "https://openminds.ebrains.eu/instances/ageCategory/perinatal",
            "embryo":      "https://openminds.ebrains.eu/instances/ageCategory/embryo",
        }
        return {
            "license":        LICENSE,
            "accessibility":  ACCESSIBILITY,
            "age_category":   AGE_CATEGORY,
        }

_MAPS = _build_maps()

def resolve_known_iri(type_key: str, raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.strip()
    if r.startswith("http://") or r.startswith("https://"):
        return r

    key = _norm(r)

    if type_key == "DatasetVersion.license":
        return _MAPS["license"].get(key)

    if type_key == "DatasetVersion.accessibility":
        return _MAPS["accessibility"].get(key)

    if type_key == "SubjectState.ageCategory":
        return _MAPS["age_category"].get(key)

    return None

# Expose mapping constants
LICENSE = _MAPS["license"]
ACCESSIBILITY = _MAPS["accessibility"]
AGE_CATEGORY = _MAPS["age_category"]
__all__ = ["resolve_known_iri", "LICENSE", "ACCESSIBILITY", "AGE_CATEGORY"]
