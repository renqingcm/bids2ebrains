# bids2ebrains

A user-friendly tool that transforms BIDS metadata into openMINDS-compliant JSON-LD, detects and completes missing information (with controlled vocabularies), and prepares datasets for submission to the EBRAINS Knowledge Graph. Use it via a Streamlit UI or a headless CLI.

## Features

- **Convert**: BIDS ➜ openMINDS JSON-LD (via `bids2openminds`)
- **Scan**: detect missing required fields across all JSON-LD files
- **Patch**: fill missing values using:
  - pick-lists for controlled terms (`License`, `Accessibility`, `AgeCategory`)
  - free-text for plain strings
  - or paste full IRIs (advanced)
- Validate - check JSON-LD files against openMINDS schemas
- **Upload**: push the patched JSON-LD to an EBRAINS KG space
- **Two interfaces**: graphical Streamlit UI and CLI with identical functionality

## Installation

Pick one of the install paths below, extras are optional add-ons.

Core CLI only
```bash
pip install bids2ebrains
```

With Streamlit UI
```bash
pip install "bids2ebrains[ui]"
```

With KG helpers (fairgraph)
```bash
pip install "bids2ebrains[kg]"
```

Everything (UI + KG helpers)
```bash
pip install "bids2ebrains[all]"
```

Developer / local checkout
```bash
# clone the repo, then from the repo root:
pip install -e .
```

## Quick Start (CLI)

```bash
# 1) Convert BIDS to JSON-LD
bids2ebrains convert --bids <BIDS_DIR> --out <JSONLD_DIR>

# 2) Scan for missing mandatory fields
bids2ebrains scan --jsonld <JSONLD_DIR>

# 3) Patch missing fields (labels or full IRIs accepted)
bids2ebrains patch --jsonld <JSONLD_DIR> \
  --set DatasetVersion.license="CC BY 4.0" \
  --set DatasetVersion.accessibility="freeAccess" \
  --set DatasetVersion.versionIdentifier="v1.0.0" \
  --set SubjectState.ageCategory="youngAdult"

# (Optional) Privacy / cohort mode: group Subjects into a single GroupSubject
bids2ebrains group --jsonld <JSONLD_DIR> --label cohort-1 --drop-individuals

# 4) Validate JSON-LD against openMINDS schema
bids2ebrains validate --jsonld <JSONLD_DIR>

# 5) Upload to the EBRAINS KG
export EBRAINS_TOKEN=...   
bids2ebrains upload --jsonld <JSONLD_DIR> --space <SPACE>  
```

## Quick Start (UI)

If you installed with the UI extra, launch from the repo folder:
```bash
# from the repository root (contains streamlit_app.py)
python -m streamlit run streamlit_app.py
```
**Step 1 – Convert**
- No local BIDS data? Click “Download ds001 example” (requires git) or upload a BIDS .zip.
- Set Output JSON-LD folder (e.g., `openminds-out`) and click **Convert**.
- A quick summary of datasets, subjects, and files is shown.
- (Optional) Enable cohort output to create GroupSubject + SubjectGroupState.

**Step 2 – Scan & Patch**
- Click **Scan** to list missing fields.
- Fill in values under Fill required fields:
 - Pick-lists for `DatasetVersion.license`, `DatasetVersion.accessibility`, `SubjectState.ageCategory`
 - Or paste IRIs manually
 - Free-text inputs for other fields (e.g., `Dataset.description`)
- (Optional) Add Custodians (Persons) with IRI/ORCID/name. Enable disambiguation to avoid duplicates via fairgraph.
- Click Patch.
- Click Validate JSON-LD to run schema checks.

**Step 3 – Upload**
- Set KG space, provide EBRAINS token (or via EBRAINS_TOKEN), then Upload.
- Use --dry-run to simulate uploads without writing to the KG.
- Upload is blocked if validation fails.

## Tokens & environment

EBRAINS_TOKEN - personal access token used for disambiguation (fairgraph) and for upload.
- Set once per shell session:
 - export EBRAINS_TOKEN=...

## Controlled Terms

Built-in pick-lists (UI) and label⇄IRI mappings (CLI/UI) cover:
- `DatasetVersion.license`
- `DatasetVersion.accessibility`
- `SubjectState.ageCategory`
You can also paste canonical IRIs directly and mappings can be extended in `bids2ebrains/mappings.py`.

## Cohort / privacy mode (optional)

Some users prefer cohort-level metadata for privacy. The group transformer produces:
- `GroupSubject` (single cohort node)
- `SubjectGroupState` (cohort state)
- Rewrites references that previously pointed to Subject/SubjectState to point to the cohort nodes.
- Optionally drops individual Subject/SubjectState files.

CLI:
```bash
bids2ebrains group --jsonld <JSONLD_DIR> --label cohort-1 --drop-individuals
```

## Validation
Validation uses the openMINDS Python library. In the UI, errors are shown with the file path and a short reason; in the CLI, use:
```bash
bids2ebrains validate --jsonld <JSONLD_DIR>
```
Upload is refused if validation fails.

## Requirements
- Python ≥ 3.9
- See [`requirements.txt`](requirements.txt)
- *Optional*: install `openMINDS_Python` to auto-load vocabularies

## License
MIT — see [LICENSE](LICENSE)