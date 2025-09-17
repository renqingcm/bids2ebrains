from __future__ import annotations

import json, os, uuid, re, yaml
from pathlib import Path
from typing import Optional, Dict, List, Union, Any

from .config import OM_VOCAB, OM_CORE
from .mappings import resolve_known_iri
from .utils import sha256_and_size, local_name, is_iri
from .resolver import resolve_person_iri
from .scanner import Scanner 

class Patcher:
    def __init__(self, jsonld_dir: Path):
        self.jsonld_dir = jsonld_dir

    @staticmethod
    def kgid() -> str:
        return f"https://kg.ebrains.eu/api/instances/{uuid.uuid4()}"

    @staticmethod
    def _type_name(payload_or_type) -> Optional[str]:
        t = payload_or_type
        if isinstance(t, dict):
            t = t.get("@type")
        if isinstance(t, str):
            return local_name(t)
        if isinstance(t, list) and t:
            return local_name(t[-1])
        return None

    @staticmethod
    def _last12_from_uuidish(s: str) -> str:
        if not s:
            return ""
        tail = s.rsplit("/", 1)[-1]
        cleaned = re.sub(r"[^0-9A-Za-z]", "", tail)
        return cleaned[-12:] if cleaned else ""

    @classmethod
    def _compute_dsv_suffix(cls, jsonld_dir: Path) -> str:
        try:
            for fp in jsonld_dir.glob("*.jsonld"):
                payload = json.loads(fp.read_text())
                t = payload.get("@type")
                if isinstance(t, list) and t:
                    t = t[-1]
                if isinstance(t, str) and local_name(t) == "DatasetVersion":
                    return cls._last12_from_uuidish(payload.get("@id", ""))
        except Exception:
            pass
        return ""

    @staticmethod
    def _normalize_orcid(orcid: Optional[str]) -> Optional[Dict[str, str]]:
        if not orcid:
            return None
        s = str(orcid).strip()
        if s.startswith("http://") or s.startswith("https://"):
            if "orcid.org" in s:
                return {"@id": s}
            return None
        if re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", s, flags=re.I):
            return {"@id": f"https://orcid.org/{s}"}
        return None

    @staticmethod
    def _parse_custodian_specs(raw) -> List[Union[str, Dict[str, str]]]:
        specs: List[Union[str, Dict[str, str]]] = []
        if raw is None:
            return specs
        if isinstance(raw, str):
            s = raw.strip()
            if s.startswith("http://") or s.startswith("https://"):
                return [s]
            try:
                loaded = json.loads(s)
                return Patcher._parse_custodian_specs(loaded)
            except Exception:
                pass
            parts = dict(
                p.split("=", 1) for p in [x.strip() for x in s.split(",")] if "=" in p
            ) if "," in s else {}
            if parts:
                return [{
                    "first": parts.get("first") or parts.get("given") or "",
                    "last": parts.get("last") or parts.get("family") or "",
                    "orcid": parts.get("orcid") or "",
                }]
            return specs

        if isinstance(raw, dict):
            if "first" in raw or "last" in raw or "orcid" in raw:
                return [raw]
            if "custodian" in raw:
                return Patcher._parse_custodian_specs(raw["custodian"])
            if "custodians" in raw:
                return Patcher._parse_custodian_specs(raw["custodians"])
            return specs

        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, (str, dict)):
                    specs.extend(Patcher._parse_custodian_specs(item))
            return specs

        return specs

    @staticmethod
    def _create_person_jsonld(first: str, last: str, orcid: Optional[str], out_dir: Path) -> Dict[str, Any]:
        pid = Patcher.kgid()
        person = {
            "@context": {"@vocab": OM_VOCAB},
            "@id": pid,
            "@type": f"{OM_CORE}Person",
            "firstName": first.strip(),
            "familyName": last.strip(),
        }
        orcid_id = Patcher._normalize_orcid(orcid)
        if orcid_id:
            person["orcid"] = orcid_id
        fname = f"person_{re.sub(r'[^a-z0-9]+','-', last.strip().lower())}_" \
                f"{re.sub(r'[^a-z0-9]+','-', first.strip().lower())}.jsonld"
        (out_dir / fname).write_text(json.dumps(person, indent=2))
        return {"@id": pid}

    @staticmethod
    def _load_answers(answers_file: Optional[Path]) -> Dict[str, str]:
        if not answers_file:
            return {}
        text = answers_file.read_text()
        if answers_file.suffix.lower() in (".yml", ".yaml"):
            return yaml.safe_load(text) or {}
        return json.loads(text)

    @staticmethod
    def _apply_answers_to_value(type_key: str, raw: str):
        iri = resolve_known_iri(type_key, raw)
        if iri:
            return {"@id": iri}
        if is_iri(raw):
            return {"@id": raw}
        return raw

    def scan(self):
        return Scanner.scan(self.jsonld_dir)

    def patch(
        self,
        repo_iri: str,
        hosted_by_iri: str = "https://kg.ebrains.eu/instances/organizationalUnit/ebrains",
        answers: Optional[Dict[str, str]] = None,
        answers_file: Optional[Path] = None,
        interactive: bool = False,
        resolve_persons: bool = False,
        token: Optional[str] = None,
    ):

        repo_iri = repo_iri or "unused://local-placeholder"
        answers = {**(self._load_answers(answers_file)), **(answers or {})}

        repo_id = self.kgid()
        label = repo_iri.rstrip("/").rsplit("/", 1)[-1] or "primary-repository"
        repo_stub = {
            "@context": {"@vocab": OM_VOCAB},
            "@id": repo_id,
            "@type": f"{OM_CORE}FileRepository",
            "IRI": repo_iri,
            "hostedBy": {"@id": hosted_by_iri},
            "label": label,
        }
        (self.jsonld_dir / "_file_repository_stub.jsonld").write_text(json.dumps(repo_stub, indent=2))

        report, prompts = Scanner.scan(self.jsonld_dir)

        if interactive:
            for type_key, question in prompts.items():
                if type_key not in answers:
                    answers[type_key] = input(question).strip()

        dsv_suffix = self._compute_dsv_suffix(self.jsonld_dir)

        cust_specs = self._parse_custodian_specs(
            answers.get("custodians", answers.get("Dataset.custodian"))
        )

        for fp, missing in report.items():
            obj = json.loads(Path(fp).read_text())
            typ = self._type_name(obj)
            if not typ:
                continue

            for key in missing:
                tkey = f"{typ}.{key}"
                if tkey in answers and answers[tkey]:
                    obj[key] = self._apply_answers_to_value(tkey, answers[tkey])

            if typ == "File":
                obj.setdefault("fileRepository", {"@id": repo_id})
                if "IRI" in obj and isinstance(obj["IRI"], str):
                    real = obj["IRI"].replace("file://", "")
                    if os.path.exists(real):
                        digest, size = sha256_and_size(real)
                        obj["storageSize"] = {
                            "@type": f"{OM_CORE}QuantitativeValue",
                            "unit": {"@id": "https://openminds.ebrains.eu/instances/unitOfMeasurement/byte"},
                            "value": size,
                        }
                        obj.setdefault("hash", []).append(
                            {"@type": f"{OM_CORE}Hash", "algorithm": "SHA-256", "digest": digest}
                        )

            # normalize lookupLabel for Subject/SubjectState when internalIdentifier present
            try:
                if dsv_suffix:
                    if typ == "Subject":
                        internal_id = obj.get("internalIdentifier") or obj.get("bidsSubjectIdentifier")
                        if isinstance(internal_id, str) and internal_id.strip():
                            obj["lookupLabel"] = f"dsv_{dsv_suffix}_{internal_id.strip()}"
                    elif typ == "SubjectState":
                        internal_id = obj.get("internalIdentifier") or obj.get("bidsSubjectIdentifier_bidsSessionIdentifier")
                        if isinstance(internal_id, str) and internal_id.strip():
                            obj["lookupLabel"] = f"dsv_{dsv_suffix}_{internal_id.strip()}"
            except Exception:
                pass

            # custodians
            try:
                if typ == "Dataset" and cust_specs:
                    current = obj.get("custodian")
                    if not isinstance(current, list):
                        current = [] if current is None else [current]

                    new_links: List[Dict[str, str]] = []
                    for spec in cust_specs:
                        if isinstance(spec, str) and (spec.startswith("http://") or spec.startswith("https://")):
                            new_links.append({"@id": spec})
                            continue

                        if isinstance(spec, dict):
                            first = (spec.get("first") or spec.get("given") or "").strip()
                            last = (spec.get("last") or spec.get("family") or "").strip()
                            orcid_raw = (spec.get("orcid") or "").strip()
                            if not first or not last:
                                continue

                            linked = None
                            if resolve_persons:
                                iri = resolve_person_iri(first, last, orcid_raw, token=token)
                                if iri:
                                    linked = {"@id": iri}
                            if linked is None:
                                linked = self._create_person_jsonld(first, last, orcid_raw, self.jsonld_dir)
                            new_links.append(linked)

                    seen = {link.get("@id") for link in current if isinstance(link, dict)}
                    for link in new_links:
                        if link.get("@id") not in seen:
                            current.append(link)
                            seen.add(link.get("@id"))

                    obj["custodian"] = current
            except Exception:
                pass

            Path(fp).write_text(json.dumps(obj, indent=2))
