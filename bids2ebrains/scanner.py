from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import json

class Scanner:
    MANDATORY: Dict[str, List[str]] = {
        "Dataset":        ["shortName", "description", "custodian"],
        "DatasetVersion": [
            "versionIdentifier",
            "versionInnovation",
            "accessibility",
            "license",
            # fullDocumentation and digitalIdentifier are optional at registration
            "dataType", "preparationDesign", "ethicsAssessment", "studyTarget", "keyword"
        ],
        "FileRepository": ["IRI", "hostedBy", "label"],
        "File": ["fileRepository", "storageSize", "hash"],
        "Subject": ["species"],
        "SubjectState": ["ageCategory"],
        "BehaviouralProtocol": ["label", "description"],
    }

    @staticmethod
    def _type_name(payload) -> str | None:
        t = payload.get("@type")
        if isinstance(t, list) and t:
            t = t[-1]
        if isinstance(t, str):
            return t.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        return None

    @classmethod
    def scan(cls, jsonld_dir: Path) -> Tuple[Dict[Path, List[str]], Dict[str, str]]:
        report: Dict[Path, List[str]] = {}
        prompts: Dict[str, str] = {}
        for fp in jsonld_dir.glob("*.jsonld"):
            payload = json.loads(fp.read_text())
            typ = cls._type_name(payload)
            if not typ:
                continue
            must = cls.MANDATORY.get(typ, [])
            miss = [k for k in must if k not in payload or payload[k] in ("", [], None)]
            if miss:
                report[fp] = miss
                for k in miss:
                    prompts.setdefault(f"{typ}.{k}", f"Enter value for {typ}.{k}: ")
        return report, prompts
