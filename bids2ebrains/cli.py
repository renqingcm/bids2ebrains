from __future__ import annotations
import argparse, sys, json, logging
import os
from pathlib import Path
from .core import convert_bids, scan_missing, patch_openminds, upload_to_kg, group_subjects, validate_jsonld

def parse_sets(items):
    result = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--set expects Type.key=value, got: {item}")
        left, value = item.split("=", 1)
        left = left.strip().replace(":", ".", 1) 
        if "." not in left:
            raise SystemExit(f"--set expects Type.key=value, got: {item}")
        result[left] = value.strip()
    return result


def main(argv=None):
    p = argparse.ArgumentParser(prog="bids2ebrains", description="BIDS - openMINDS - EBRAINS KG")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    sub = p.add_subparsers(dest="cmd", required=True)

    # convert
    pc = sub.add_parser("convert", help="Convert BIDS - openMINDS JSON-LD")
    pc.add_argument("--bids", required=True, type=Path)
    pc.add_argument("--out",  required=True, type=Path)

    # scan
    ps = sub.add_parser("scan", help="Scan JSON-LD for missing mandatory fields")
    ps.add_argument("--jsonld", required=True, type=Path)

    # patch
    pp = sub.add_parser("patch", help="Patch missing fields (answers + repo)")
    pp.add_argument("--resolve-persons", action="store_true",
                help="Try to match existing Person entries in EBRAINS (fairgraph) before creating new ones.")
    pp.add_argument("--token", help="EBRAINS token for fairgraph lookups (or set EBRAINS_TOKEN env var)")

    pp.add_argument("--jsonld", required=True, type=Path)
    pp.add_argument("--repo-iri", default="", help="Optional. Only used for error handling.")
    pp.add_argument("--hosted-by-iri", default="https://kg.ebrains.eu/instances/organizationalUnit/ebrains")
    pp.add_argument("--set", action="append",
                help="Set a value for a missing field. Use Type.key=value (or Type:key=value). Repeatable.")
    pp.add_argument("--answers-file", type=Path)
    pp.add_argument("--interactive", action="store_true")

    # group
    pg = sub.add_parser("group", help="Convert Subject/SubjectState to GroupSubject/SubjectGroupState")
    pg.add_argument("--jsonld", required=True, type=Path)
    pg.add_argument("--label", help="Label for the group (default: cohort-1)")
    pg.add_argument("--keep-individuals", action="store_true", help="Keep original Subject/SubjectState files")

    # validate
    pv = sub.add_parser("validate", help="Validate JSON-LD against openMINDS schema")
    pv.add_argument("--jsonld", required=True, type=Path)

    # upload
    pu = sub.add_parser("upload", help="Upload JSON-LD to EBRAINS KG")
    pu.add_argument("--jsonld", required=True, type=Path)
    pu.add_argument("--space", required=True)
    pu.add_argument("--token")
    pu.add_argument("--no-overwrite", dest="overwrite", action="store_false")
    pu.add_argument("--dry-run", action="store_true")
    pu.add_argument("--keep-controlled", dest="skip_controlled", action="store_false")

    args = p.parse_args(argv)

    if args.cmd == "convert":
        convert_bids(args.bids, args.out)
        return 0

    if args.cmd == "scan":
        report, prompts = scan_missing(args.jsonld)
        missing = {str(fp): miss for fp, miss in report.items()}
        print(json.dumps({"missing": missing, "prompts": prompts}, indent=2))
        return 0

    if args.cmd == "patch":
        answers = parse_sets(args.set)
        patch_openminds(
        args.jsonld,
        repo_iri=args.repo_iri,
        hosted_by_iri=args.hosted_by_iri,
        answers=answers,
        answers_file=args.answers_file,
        interactive=args.interactive,
        resolve_persons=args.resolve_persons,
        token=(args.token or os.getenv("EBRAINS_TOKEN")),
    )
        return 0
    
    if args.cmd == "group":
        group_subjects(args.jsonld, label=args.label, keep_individuals=args.keep_individuals)
        return 0
    
    if args.cmd == "validate":
        errs = validate_jsonld(args.jsonld)
        if not errs:
            print("OK: no schema validation errors")
            return 0
        for fp, msg in errs:
            print(f"[invalid] {fp}: {msg}")
        return 1

    if args.cmd == "upload":
        try:
            upload_to_kg(
                args.jsonld, space=args.space, token=args.token,
                overwrite=args.overwrite, dry_run=args.dry_run,
                skip_controlled_terms=not args.keep_controlled
            )
            return 0
        except Exception as e:
            logging.error("Upload failed: %s", e)
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

if __name__ == "__main__":
    raise SystemExit(main())
