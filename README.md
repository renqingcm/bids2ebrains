# Automating BIDS Dataset Registration into the EBRAINS Knowledge Graph

**Google Summer of Code – Final Report (Renqing Cuomao)**

A user-friendly toolchain to transform BIDS metadata into openMINDS-compliant JSON-LD, detect and complete missing information, validate locally, and upload to the EBRAINS Knowledge Graph (KG). Usable via a Streamlit UI and a CLI with matching features.

---

## 1) Project Goals

- Convert BIDS metadata → openMINDS JSON-LD.
- Help users fill mandatory fields (with pick-lists for common controlled terms).
- Validate locally before upload.
- Upload JSON-LD to an EBRAINS KG space with clear feedback.
- Provide a small, composable Python API plus a clean UI/CLI.

---

## 2) What I built

### End-to-end pipeline

- **Convert** – wraps `bids2openminds`; assigns EBRAINS-style `@id`s where needed (`converter.py`).
- **Scan** – detects missing mandatory fields for each type (`scanner.py`).
- **Patch** – applies user answers (UI form, CLI `--set`, or answers file); creates a `FileRepository` stub; computes SHA-256 + size for local files; supports custodian creation or ORCID disambiguation; normalizes `lookupLabels` (`patcher.py`).
- **Validate** – two-stage validator (`validator.py`):
  - Try `openMINDS.Collection` for schema checks (full mode).
  - If not available, run a robust fallback (readable JSON, `@id/@type`, and all mandatory fields). The UI displays the validation mode used.
- **Upload** – posts/puts to the EBRAINS KG with overwrite support and skips controlled-term instance files (`uploader.py`).
- **Group utility** – optional Subject → GroupSubject conversion (`grouper.py`).

### Interfaces

- **CLI (`bids2ebrains`)** – see quick start below.
- **Streamlit UI** – 3 steps: Convert → Scan & Patch → Upload, with a `ds001` “one-click” download or local zip import and clear validation results (`streamlit_app.py`).

### Controlled terms (built-in pick-lists)

- `DatasetVersion.license`
- `DatasetVersion.accessibility`
- `SubjectState.ageCategory`

> For other fields that ultimately require IRIs in openMINDS (e.g., `preparationDesign`, `keyword`, `studyTarget`), the UI currently accepts free text to unblock users; see _What’s left to do_.

---

## 3) Current State

- Works end-to-end on standard BIDS examples (e.g., `ds001`): Convert → Scan/Patch → Validate → Upload.
- UI shows “Schema validation passed” and indicates Validation mode (full-openMINDS vs basic-fallback).
- Repository metadata is always written (stub + linking), avoiding spurious scan warnings.
- Custodians: link by IRI, match by ORCID, or create a `Person` JSON-LD; `fairgraph` disambiguation.

---

## 4) What’s left to do

- Autocomplete pickers for `DatasetVersion.preparationDesign`, `keyword`, `studyTarget`, and a proper linked `EthicsAssessment` object (instead of a plain note).
- Strict validation mode (opt-in): fail when full openMINDS ingestion is unavailable (no fallback).
- CI/tests: JSON-LD fixtures for pass/fail, unit tests for `scanner`/`patcher`/`validator`/`uploader`.
- Packaging/docs: pin a known-good openMINDS version or provide an environment file; add screenshots & troubleshooting.

---

## 5) Repository & Code Status

- **Main branch**: https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/tree/main  
- **Development branch**: https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/tree/dev  
- **GSoC final snapshot tag**: [`gsoc25-final`](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/tree/gsoc25-final)

### Key files (permalinks)

- [Validator](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/blob/gsoc25-final/bids2ebrains/validator.py)
- [Patcher](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/blob/gsoc25-final/bids2ebrains/patcher.py)
- [CLI](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/blob/gsoc25-final/bids2ebrains/cli.py)
- [UI](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/blob/gsoc25-final/streamlit_app.py)
- [Commit log](https://gitlab.ebrains.eu/ri/projects-and-initiatives/bids2ebrains/bids2ebrains/-/commits/gsoc25-final)

---

## 6) Challenges & What I learned

- **Version drift & APIs**: different openMINDS versions expose different ingestion methods. I designed a resilient validator that tries multiple code paths and falls back safely while still guaranteeing structural correctness.
- **Human-in-the-loop metadata**: many fields can’t be inferred from BIDS; the guided patching flow (with pick-lists where feasible) meaningfully improves metadata quality and user success.
- **KG upload ergonomics**: added overwrite handling, controlled-term skipping, and clear error reporting to speed up iteration.

---

## 7) How to Use

### Install

```bash
# CLI only
pip install bids2ebrains

# With Streamlit UI
pip install "bids2ebrains[ui]"

# With KG helpers (fairgraph)
pip install "bids2ebrains[kg]"

# Everything
pip install "bids2ebrains[all]"
```

---

## 7) Quick Start (CLI)

```bash
# 1) Convert BIDS → JSON-LD
bids2ebrains convert --bids <BIDS_DIR> --out <JSONLD_DIR>

# 2) Scan for missing mandatory fields
bids2ebrains scan --jsonld <JSONLD_DIR>

# 3) Patch missing fields (labels or IRIs accepted)
bids2ebrains patch --jsonld <JSONLD_DIR> \
  --set DatasetVersion.license="CC BY 4.0" \
  --set DatasetVersion.accessibility="freeAccess" \
  --set DatasetVersion.versionIdentifier="v1.0.0" \
  --set SubjectState.ageCategory="youngAdult"

# 4) Validate locally
bids2ebrains validate --jsonld <JSONLD_DIR>

# 5) Upload to the EBRAINS KG
export EBRAINS_TOKEN=...   
bids2ebrains upload --jsonld <JSONLD_DIR> --space <SPACE>
```

---

## 8) Quick Start (Streamlit UI)
```bash
python -m streamlit run streamlit_app.py
```
Step 1 – Convert: download ds001 or upload a BIDS .zip; choose an output folder; Convert.

Step 2 – Scan & Patch: Scan, fill required fields (pick-lists for license/accessibility/age; free text for the rest), Patch, Validate JSON-LD.

Step 3 – Upload: Ensure your EBRAINS_TOKEN is already set once in your environment (e.g., export EBRAINS_TOKEN=<your_token> in your shell). Then specify the target space and click Upload.

---

## 9) Example Outputs (redacted IDs)
FileRepository stub
```bash
{
  "@context": {"@vocab": "https://openminds.ebrains.eu/vocab/"},
  "@id": "https://kg.ebrains.eu/api/instances/<uuid>",
  "@type": "https://openminds.ebrains.eu/core/FileRepository",
  "IRI": "unused://local-placeholder",
  "hostedBy": {"@id": "https://kg.ebrains.eu/instances/organizationalUnit/ebrains"},
  "label": "local-placeholder"
}
```
DatasetVersion (excerpt)
```bash
{
  "@context": {"@vocab": "https://openminds.ebrains.eu/vocab/"},
  "@id": "https://kg.ebrains.eu/api/instances/<uuid>",
  "@type": "https://openminds.ebrains.eu/core/DatasetVersion",
  "accessibility": {"@id": "https://openminds.ebrains.eu/instances/productAccessibility/freeAccess"},
  "license": {"@id": "https://openminds.ebrains.eu/instances/licenses/CC-BY-4.0"},
  "versionIdentifier": "v1.0.0",
  "experimentalApproach": [{"@id": "https://openminds.ebrains.eu/instances/experimentalApproach/neuroimaging"}],
  "technique": [{"@id": "https://openminds.ebrains.eu/instances/technique/structuralMagneticResonanceImaging"}]
}
```

---

## 10) License

**MIT** — see `LICENSE`

---

## How others can extend this work

- Use the core API in `bids2ebrains/core.py` (`convert_bids`, `scan_missing`, `patch_openminds`, `validate_jsonld`, `upload_to_kg`, `group_subjects`) to script custom flows.
- Implement additional pickers (autocomplete) for `preparationDesign`, `keyword`, `studyTarget`, and a proper `EthicsAssessment` object creator.
- Refine the UI for more functionality and polish.
- Contribute tests and fixtures (see “What’s left to do”).

---

## Acknowledgements

Thanks to mentors and collaborators for guidance and feedback throughout: **Lyuba Zehl**, **Raphaël Gazzotti**, **Cyril Pernet**, **Peyman Najafi**, **Sophia Pieschnik**, **Andrew P. Davison**, **Oliver Schmid**.