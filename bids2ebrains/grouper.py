from __future__ import annotations
from pathlib import Path
from typing import Optional
import json, uuid
from .config import OM_VOCAB, OM_CORE
from .utils import local_name

def _kgid() -> str:
    return f"https://kg.ebrains.eu/api/instances/{uuid.uuid4()}"

def group_subjects(jsonld_dir: Path, label: Optional[str] = None, keep_individuals: bool = False) -> None:
    label = label or "cohort-1"
    subjects, states, others = [], [], []

    for fp in jsonld_dir.glob("*.jsonld"):
        try:
            obj = json.loads(fp.read_text())
        except Exception:
            continue
        t = obj.get("@type")
        if isinstance(t, list): t = t[-1]
        if isinstance(t, str): t = local_name(t)
        if t == "Subject":
            subjects.append((fp, obj))
        elif t == "SubjectState":
            states.append((fp, obj))
        else:
            others.append((fp, obj))

    if not subjects and not states:
        return

    species = next((s[1].get("species") for s in subjects if s[1].get("species")), None)

    group_id = _kgid()
    group = {
        "@context": {"@vocab": OM_VOCAB},
        "@id": group_id,
        "@type": f"{OM_CORE}GroupSubject",
        "label": label,
    }
    if species:
        group["species"] = species

    state_id = _kgid()
    age = next((st[1].get("ageCategory") for st in states if st[1].get("ageCategory")), None)
    group_state = {
        "@context": {"@vocab": OM_VOCAB},
        "@id": state_id,
        "@type": f"{OM_CORE}SubjectGroupState",
        "label": f"{label}_state",
    }
    if age:
        group_state["ageCategory"] = age

    (jsonld_dir / "group_subject.jsonld").write_text(json.dumps(group, indent=2))
    (jsonld_dir / "group_subject_state.jsonld").write_text(json.dumps(group_state, indent=2))

    subject_ids = {o["@id"] for _, o in subjects if "@id" in o}
    state_ids   = {o["@id"] for _, o in states if "@id" in o}

    def retarget(v):
        if isinstance(v, dict) and "@id" in v:
            if v["@id"] in subject_ids: return {"@id": group_id}
            if v["@id"] in state_ids:   return {"@id": state_id}
        if isinstance(v, list): return [retarget(x) for x in v]
        return v

    for fp, obj in others:
        changed = False
        for k,v in list(obj.items()):
            nv = retarget(v)
            if nv is not v:
                obj[k] = nv
                changed = True
        if changed:
            fp.write_text(json.dumps(obj, indent=2))

    if not keep_individuals:
        for fp,_ in subjects + states:
            fp.unlink(missing_ok=True)
