from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .converter import Converter
from .scanner import Scanner
from .patcher import Patcher as _PatcherClass
from .uploader import Uploader as _UploaderClass
from .grouper import group_subjects as _group_subjects
from .validator import validate_dir as _validate_dir

def group_subjects(jsonld_dir: Path, label: Optional[str] = None, keep_individuals: bool = False) -> None:
    return _group_subjects(jsonld_dir, label=label, keep_individuals=keep_individuals)

def convert_bids(bids_root: Path, out_dir: Path) -> None:
    return Converter.convert(bids_root, out_dir)

def scan_missing(jsonld_dir: Path) -> Tuple[Dict[Path, List[str]], Dict[str, str]]:
    return Scanner.scan(jsonld_dir)

def patch_openminds(
    jsonld_dir: Path,
    repo_iri: str,
    hosted_by_iri: str = "https://kg.ebrains.eu/instances/organizationalUnit/ebrains",
    answers: Optional[Dict[str, str]] = None,
    answers_file: Optional[Path] = None,
    interactive: bool = False,
    resolve_persons: bool = False,
    token: Optional[str] = None,
) -> None:
    return _PatcherClass(jsonld_dir).patch(
        repo_iri=repo_iri,
        hosted_by_iri=hosted_by_iri,
        answers=answers,
        answers_file=answers_file,
        interactive=interactive,
        resolve_persons=resolve_persons,
        token=token,
    )

def validate_jsonld(jsonld_dir: Path):
    return _validate_dir(jsonld_dir)

def upload_to_kg(
    jsonld_dir: Path,
    space: str,
    token: Optional[str] = None,
    overwrite: bool = True,
    skip_controlled_terms: bool = True,
    dry_run: bool = False,
) -> None:
    return _UploaderClass(space=space, token=token).upload_dir(
        jsonld_dir=jsonld_dir,
        overwrite=overwrite,
        skip_controlled_terms=skip_controlled_terms,
        dry_run=dry_run,
    )
