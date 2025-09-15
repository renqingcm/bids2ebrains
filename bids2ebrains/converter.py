from __future__ import annotations
from pathlib import Path
import bids2openminds.converter as bm
import uuid

def _kgid() -> str:
    return f"https://kg.ebrains.eu/api/instances/{uuid.uuid4()}"

class Converter:
    @staticmethod
    def convert(bids_root: Path, out_dir: Path) -> None:
        out_dir.mkdir(exist_ok=True, parents=True)
        collection = bm.convert(str(bids_root), save_output=False, multiple_files=True)
        for obj in collection:
            if isinstance(obj.id, str) and obj.id.startswith("_:"):
                obj.id = _kgid()
        collection.save(out_dir, individual_files=True)
