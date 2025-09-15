# bids2ebrains

A user-friendly tool that transforms BIDS metadata into openMINDS-compliant JSON-LD, detects and completes missing information (with controlled vocabularies), and prepares datasets for submission to the EBRAINS Knowledge Graph. Use it via a Streamlit UI or a headless CLI.

## ✨ Features

- **Convert**: BIDS ➜ openMINDS JSON-LD (via `bids2openminds`)
- **Scan**: detect missing required fields across all JSON-LD files
- **Patch**: fill missing values using:
  - pick-lists for controlled terms (`License`, `Accessibility`, `AgeCategory`)
  - free-text for plain strings
  - or paste full IRIs (advanced)
- **Upload**: push the patched JSON-LD to an EBRAINS KG space
- **UI & CLI**: same pipeline, two interfaces

## 🧰 Installation

```bash
# (optional) create and activate a virtualenv or conda env
pip install -e .
```

Notes:
- openMINDS is used for schema/instances; bids2openminds does the BIDS→openMINDS conversion.
- To silence a Pandas warning you may also pip install bottleneck.

## 🚀 Quick Start (UI)

```bash
streamlit run streamlit_app.py
```
Step 1 – Convert
- No local BIDS data? Click “Download ds001 example” (requires git) or upload a BIDS .zip.
- Set Output JSON-LD folder (e.g., openminds-out) and click Convert.

Step 2 – Scan & Patch
- Click Scan to list missing fields.
- In Fill required fields, provide values:
 - Pick-lists for DatasetVersion.license, DatasetVersion.accessibility, SubjectState.ageCategory
 - Or choose Enter IRI manually to paste a canonical IRI
 - Text inputs for other fields (e.g., DatasetVersion.versionIdentifier, Dataset.description, ...)

- Set Repository IRI (e.g., an EBRAINS Data-Proxy bucket URL) and click Patch.
 - The value you provide for a Type.key is applied to all files missing that same field.

Step 3 – Upload
- Set KG space (e.g., collab-bids2ebrains-test)
- Provide EBRAINS token (or set via EBRAINS_TOKEN environment variable)
- Optionally enable Dry run, then click Upload

## 🧑‍💻 Quick Start (CLI)

```bash
# Convert BIDS to JSON-LD
python -m bids2ebrains.cli convert --bids <BIDS_DIR> --out <JSONLD_DIR>

# Scan for missing required fields
python -m bids2ebrains.cli scan --jsonld <JSONLD_DIR>

# Patch missing fields (labels or full IRIs accepted)
python -m bids2ebrains.cli patch --jsonld <JSONLD_DIR> --repo-iri <URL> \
  --set DatasetVersion.license="CC BY 4.0" \
  --set DatasetVersion.accessibility="freeAccess" \
  --set DatasetVersion.versionIdentifier="v1.0.0" \
  --set SubjectState.ageCategory="youngAdult"

# Upload to the EBRAINS KG
export EBRAINS_TOKEN=...
python -m bids2ebrains.cli upload --jsonld <JSONLD_DIR> --space <SPACE> --dry-run
```

## 🧩 Controlled Terms (labels ⇄ IRIs)

- Built-in pick-lists (UI) and label→IRI mapping (CLI/UI) cover:
 - DatasetVersion.license
 - DatasetVersion.accessibility
 - SubjectState.ageCategory
- You can also paste canonical IRIs directly.
- Extend mappings in bids2ebrains/mappings.py.

## How Scan & Patch Works

- Scan iterates all *.jsonld, reads @type, and checks required keys per type.
- Missing items are aggregated as Type.key, so you answer once per field type.
- Patch writes your value into every object missing that Type.key and, for file objects, adds hash/size and a FileRepository stub derived from your Repository IRI.

### 🖥️ Streamlit (Prototype)

```bash
streamlit run streamlit_app.py
```

## ⚙️ Advanced

- Namespaces for `@context` and OpenMINDS `@type` URIs are derived dynamically from `openMINDS_Python` (with safe fallbacks).
- You can override the KG endpoint via `EBRAINS_KG_BASE` if needed.

## 📦 Requirements
- See [`requirements.txt`](requirements.txt)
- *Optional*: install `openMINDS_Python` to automatically load controlled vocabularies and instances  

## 📄 License
MIT — see [LICENSE](LICENSE)