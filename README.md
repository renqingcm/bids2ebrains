# bids2ebrains

A user-friendly toolchain to transform BIDS metadata into EBRAINS-compliant openMINDS JSON-LD, ready for upload to the EBRAINS Knowledge Graph (KG). User can use a Streamlit UI or a CLI with matching functionality.

## 1) Installation

```bash
# CLI only
pip install bids2ebrains

# With Streamlit UI
pip install "bids2ebrains[ui]"

# With KG upload helpers (fairgraph)
pip install "bids2ebrains[kg]"

# Everything
pip install "bids2ebrains[all]"
```

## 2) Usage

### CI

```bash
# 1) Convert BIDS → JSON-LD
bids2ebrains convert --bids <BIDS_DIR> --out <JSONLD_DIR>

# 2) Scan for missing mandatory fields
bids2ebrains scan --jsonld <JSONLD_DIR>

# 3) Patch missing fields
bids2ebrains patch --jsonld <JSONLD_DIR> \
  --set DatasetVersion.license="CC BY 4.0" \
  --set DatasetVersion.accessibility="freeAccess" \
  --set SubjectState.ageCategory="youngAdult"

# 4) Validate JSON-LD
bids2ebrains validate --jsonld <JSONLD_DIR>

# 5) Upload to EBRAINS KG
export EBRAINS_TOKEN=...
bids2ebrains upload --jsonld <JSONLD_DIR> --space <SPACE>
```

### Streamlit UI

```bash
python -m streamlit run streamlit_app.py
```
The UI provides an end-to-end workflow for preparing BIDS datasets for registration in the EBRAINS Knowledge Graph:

- **Convert** - Load a BIDS dataset (local directory or the built-in `ds001`) and generate openMINDS-compliant JSON-LD with stable EBRAINS-style `@id`s.
- **Scan & Patch** – Detect missing mandatory fields and complete them through guided forms using pick-lists or free-text input.
- **Validate & Upload** - Run schema-aware validation (with automatic fallback to structural checks). After validation, set `EBRAINS_TOKEN` in your environment, choose a KG space, and upload the finalized metadata.

## 3) Contribution
Contributions are welcome. Please open an Issue or a Merge Request in this repository. (A dedicated `CONTRIBUTING.md` may be added in the future.)

## 4) License

**MIT** - see `LICENSE`

## 5) Acknowledgements

This work was developed as part of the Google Summer of Code 2025 program under the mentorship of the International Neuroinformatics Coordinating Facility (INCF). It also received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101147319 (EBRAINS 2.0).

## 6) Further Documentation

For GSoC-specific implementation notes and development details, see `gsoc25-final-report.md`.
