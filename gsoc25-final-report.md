# Automating BIDS Dataset Registration into the EBRAINS Knowledge Graph

**Google Summer of Code – Final Report (Renqing Cuomao)**

This project provides a user-friendly toolchain to represents BIDS datasets in the EBRAINS Knowlede Graph via the openMINDS schema. User can use a Streamlit UI or a CLI with matching features.

---

## 1) Project Goals

- Convert a BIDS dataset → openMINDS JSON-LD.
- detect and complete missing information --> Help users fill mandatory fields (with pick-lists for common controlled terms).
- Validate locally the josn-ld.
- Upload JSON-LD to an EBRAINS KG space with clear feedback.
- Provide a clean Python API and a simple UI/CLI for end-to-end interaction.

---

## 2) Main Contributions

### End-to-end pipeline

- **Convert** – calls `bids2openminds` and assigns EBRAINS-style `@id`s where needed (`converter.py`).
- **Scan** – detects missing mandatory fields for each openMINDS type and provides a structured list of missing information (`scanner.py`). 
- **Patch** – fills missing information using user input (UI, CLI `--set`, or answers file), creates a `FileRepository` stub, computes SHA-256 and file sizes, supports custodian ORCID matching, and normalizes `lookupLabels` (`patcher.py`).
- **Validate** – two-stage validator (`validator.py`):
  - try schema-based validation with `openMINDS.Collection`,  
  - if unavailable, fall back to a structural validation (readable JSON, `@id/@type`, and all mandatory fields). The UI reports which validatioin mode was used.
- **Upload** – uploads metadata to the EBRAINS KG with overwrite support and automatically skips controlled-term instance files (`uploader.py`).
- **Group utility** – optional Subject → GroupSubject conversion (`grouper.py`).

### Interfaces

- **CLI (`bids2ebrains`)** - full pipeline available through command-line commands, see quick start below.
- **Streamlit UI** – 3 steps: Convert → Scan & Patch → Upload, including one-click download of `ds001` or upload of a local BIDS zip (`streamlit_app.py`).

### Controlled terms (built-in pick-lists)

- `DatasetVersion.license`
- `DatasetVersion.accessibility`
- `SubjectState.ageCategory`

> For other fields that ultimately require IRIs in openMINDS (e.g., `preparationDesign`, `keyword`, `studyTarget`), the UI currently accepts free text to unblock users; see _What’s left to do_.

---

## 3) Current State

- Works end-to-end on standard BIDS examples (e.g., `ds001`).
- UI shows “Schema validation passed” and indicates Validation mode (full-openMINDS vs basic-fallback).
- Repository metadata is always written (stub + linking), avoiding spurious scan warnings.
- Custodian handling supports linking existing IRIs, ORCID matching, and creating new `Person` entries.

---

## 4) What’s left to do

- Autocomplete pickers for fields such as `DatasetVersion.preparationDesign`, `keyword`, `studyTarget`, and a proper linked `EthicsAssessment` object (instead of a plain note).
- Strict validation mode (opt-in): fail when full openMINDS ingestion is unavailable (no fallback).
- CI/tests: add JSON-LD fixtures and unit tests for scanning, patching, validation, and upload.
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

## 7) Example Outputs (redacted IDs)
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

## 8) How others can extend this work

- Use the core API in `bids2ebrains/core.py` (`convert_bids`, `scan_missing`, `patch_openminds`, `validate_jsonld`, `upload_to_kg`, `group_subjects`) to build custom workflows.
- Add autocomplete pick-lists for additional openMINDS concepts or improve the UI for more funtionality and polish.
- Add tests, fixtures, or example datasets to support more robust validation. (see “What’s left to do”).

---

## 9) Acknowledgements

Thank you to all mentors for their guidance throughout this project: **Lyuba Zehl**, **Raphaël Gazzotti**, **Cyril Pernet**, **Peyman Najafi**, **Sophia Pieschnik**, **Andrew P. Davison**, and **Oliver Schmid**.