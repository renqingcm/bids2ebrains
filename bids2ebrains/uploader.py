from __future__ import annotations
from pathlib import Path
from typing import Optional
import os, json, requests

from .config import KG_BASE

class Uploader:
    def __init__(self, space: str, token: Optional[str] = None):
        self.space = space
        self.token = token

    def upload_dir(
        self,
        jsonld_dir: Path,
        overwrite: bool = True,
        skip_controlled_terms: bool = True,
        dry_run: bool = False,
    ):
        token = self.token or os.getenv("EBRAINS_TOKEN") or os.getenv("HBP_TOKEN")
        if not token:
            raise RuntimeError("Missing token. Set EBRAINS_TOKEN.")
        if os.getenv("HBP_TOKEN") and not os.getenv("EBRAINS_TOKEN"):
            print("[warning] HBP_TOKEN is deprecated; please migrate to EBRAINS_TOKEN.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ld+json",
            "Accept": "application/ld+json",
        }

        for fp in Path(jsonld_dir).glob("*.jsonld"):
            payload = json.loads(fp.read_text())

            cid = payload.get("@id", "")
            is_controlled = any(
                d in cid
                for d in (
                    "openminds.ebrains.eu/instances/",
                    "openminds.om-i.org/instances/",
                )
            )
            if skip_controlled_terms and is_controlled:
                continue

            if dry_run:
                print("[dry-run]", fp.stem)
                continue

            post = requests.post(f"{KG_BASE}?space={self.space}", headers=headers, json=payload, timeout=30)

            if post.status_code == 409 and overwrite:
                iid = payload["@id"].split("/")[-1]
                put = requests.put(f"{KG_BASE}/{iid}?space={self.space}", headers=headers, json=payload, timeout=30)
                resp = put
            else:
                resp = post

            if resp.ok:
                print("✓", fp.stem)
            else:
                print("✗", fp.stem, resp.status_code, resp.text)
                break
