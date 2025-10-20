import os
from pathlib import Path
import streamlit as st
from bids2ebrains import convert_bids, scan_missing, patch_openminds, upload_to_kg, group_subjects, validate_jsonld
import subprocess, time
import json, zipfile, shutil
from bids2ebrains.mappings import LICENSE, ACCESSIBILITY, AGE_CATEGORY

def _local_name(uri: str) -> str:
    if not isinstance(uri, str):
        return ""
    return uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]

def _summarize_missing(report: dict) -> dict:
    counts = {}
    for fp, miss in report.items():
        try:
            payload = json.loads(Path(fp).read_text())
            typ = payload.get("@type")
            if isinstance(typ, list) and typ:
                typ = typ[-1]
            if isinstance(typ, str):
                tname = _local_name(typ)
            else:
                tname = "Unknown"
            for k in miss:
                key = f"{tname}.{k}"
                counts[key] = counts.get(key, 0) + 1
        except Exception:
            for k in miss:
                counts[k] = counts.get(k, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))

def download_ds001_sparse():
    with st.status("Downloading ds001…", expanded=True) as status:
        try:
            dest_root = Path("bids-examples")
            dest_root.mkdir(exist_ok=True)
            tmp = Path("bids-examples-sparse")
            if tmp.exists():
                shutil.rmtree(tmp)
            subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                 "https://github.com/bids-standard/bids-examples.git", str(tmp)],
                check=True, capture_output=True,
            )
            status.write("Repo cloned.")
            subprocess.run(["git", "-C", str(tmp), "sparse-checkout", "set", "ds001"],
                           check=True, capture_output=True)
            status.write("Checked out ds001.")
            target = dest_root / "ds001"
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(tmp / "ds001"), str(target))
            shutil.rmtree(tmp, ignore_errors=True)
            st.session_state["bids_dir"] = str(target)
            status.update(label=f"ds001 ready at: {target}", state="complete", expanded=False)
            time.sleep(0.3)
            st.rerun()
        except Exception as e:
            status.update(label=f"Failed to download ds001: {e}", state="error", expanded=True)

def jsonld_summary(out_dir: Path) -> dict:
    counts = {}
    for fp in Path(out_dir).glob("*.jsonld"):
        try:
            obj = json.loads(fp.read_text())
            typ = obj.get("@type")
            if isinstance(typ, list) and typ:
                typ = typ[-1]
            if isinstance(typ, str):
                name = typ.rsplit("/", 1)[-1]
            else:
                name = "Unknown"
            counts[name] = counts.get(name, 0) + 1
        except Exception:
            counts["Unreadable"] = counts.get("Unreadable", 0) + 1
    return counts

def _maybe_text(key: str, label: str, placeholder: str = "", help_text: str = ""):
    prompts = st.session_state.get("scan_prompts", {})
    if key in prompts:
        v = st.text_input(label, value="", placeholder=placeholder, key=f"k_{key.replace('.','_')}", help=help_text)
        return v.strip()
    return ""

def _check_iri_field(label: str, key: str, placeholder: str = "") -> str:
    val = st.text_input(label, key=key, placeholder=placeholder)
    if val and not (val.startswith("http://") or val.startswith("https://")):
        st.warning("That doesn't look like an IRI (should start with http:// or https://).")
    return val.strip()

st.set_page_config(page_title="BIDS – openMINDS – EBRAINS KG", page_icon="🧠", layout="wide")

css_path = Path(__file__).with_name("style.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown("<h1>BIDS → openMINDS → EBRAINS KG</h1>", unsafe_allow_html=True)


# Step 1 Convert

with st.expander("Step 1 Convert ⚙️", expanded=False):
    st.session_state.setdefault("bids_dir", "")
    st.session_state.setdefault("out_dir", "")

    st.write("If you don't have a local BIDS dataset, either download the ds001 example or add a zipped BIDS dataset from your computer (analyzed locally).")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Download ds001 example"):
            download_ds001_sparse()
    with c2:
        up = st.file_uploader(
            "Or add a local BIDS .zip (analyzed locally and no data is uploaded)",
            type="zip",
            help="Select a zipped BIDS dataset from your local machine. The archive is processed locally; nothing is uploaded."
        )

        if up is not None:
            try:
                upload_root = Path("bids-upload")
                if upload_root.exists():
                    shutil.rmtree(upload_root)
                upload_root.mkdir(parents=True, exist_ok=True)
                zip_path = upload_root / "dataset.zip"
                with open(zip_path, "wb") as f:
                    f.write(up.getbuffer())
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(upload_root)
                def _find_bids_root(base: Path) -> Path | None:
                    for p in [base, *base.glob("**/*")]:
                        if p.is_dir() and (p / "dataset_description.json").exists():
                            return p
                    return None
                root = _find_bids_root(upload_root)
                if root:
                    st.session_state["bids_dir"] = str(root)
                    st.success(f"Uploaded and extracted. Using: {root}")
                    st.rerun()
                else:
                    st.error("Could not find dataset_description.json in the uploaded archive.")
            except Exception as e:
                st.error(f"Failed to process upload: {e}")

    bids_dir = st.text_input(
        "BIDS directory",
        key="bids_dir",
        placeholder="e.g., bids-examples/ds001",
        help="Path to a local BIDS dataset. Use Download or Upload if you don't have one."
    )
    out_dir = st.text_input(
        "Output JSON-LD folder",
        key="out_dir",
        placeholder="e.g., openminds-out",
        help="Folder where the converted openMINDS JSON-LD files will be written."
    )

    if st.button("Convert"):
        if not bids_dir or not Path(bids_dir).exists():
            st.error("Please provide a valid BIDS directory (use Download or Upload).")
        elif not out_dir:
            st.error("Please provide an output folder name.")
        else:
            convert_bids(Path(bids_dir), Path(out_dir))
            st.success(f"Converted to {out_dir}")
            s = jsonld_summary(Path(out_dir))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dataset(s)", s.get("Dataset", 0))
            c2.metric("DatasetVersion(s)", s.get("DatasetVersion", 0))
            c3.metric("Subject(s)", s.get("Subject", 0))
            c4.metric("File(s)", s.get("File", 0))


# Step 2 Scan & Patch

with st.expander("Step 2 Scan & Patch 🩹"):
    jsonld = st.text_input(
        "JSON-LD folder",
        value=st.session_state.get("jsonld", "openminds-out"),
        help="Folder containing the .jsonld files produced in Step 1."
    )
    st.session_state["jsonld"] = jsonld

    interactive = st.checkbox(
        "Also allow terminal prompts (CLI style)",
        value=False,
        help="If enabled and a field remains missing, the program will ask for it in the terminal when running headless."
    )
    if st.button("Scan"):
        rep, prompts = scan_missing(Path(jsonld))
        st.session_state["scan_report"] = {str(k): v for k, v in rep.items()}
        st.session_state["scan_prompts"] = prompts
        miss_summary = _summarize_missing(rep)
        n_files_with_issues = len([1 for v in rep.values() if v])
        n_total_gaps = sum(len(v) for v in rep.values())
        st.success(f"{n_files_with_issues} files have missing fields; {n_total_gaps} total gaps.")
        st.markdown("**Aggregated by Type.key (count):**")
        if miss_summary:
            ordered_missing = sorted(
                miss_summary.items(),
                key=lambda item: (-item[1], item[0])
            )
            for type_key, count in ordered_missing:
                st.write(f"- `{type_key}` : {count}")
        else:
            st.write("No missing fields detected.")
        with st.expander("Missing fields per file"):
            st.json(st.session_state["scan_report"])
        with st.expander("Unique prompts"):
            st.json(st.session_state["scan_prompts"])

    st.subheader("Fill required fields")
    prompts = st.session_state.get("scan_prompts", {})
    auto_filled = {"FileRepository.hostedBy", "FileRepository.label"}
    for k in list(prompts.keys()):
        if k in auto_filled:
            prompts.pop(k, None)

    st.caption(
        "Note: SubjectState internal identifiers are expected from the converter. "
        "If they are missing, upgrade the converter; "
        "lookup labels will be auto-generated here once identifiers exist."
    )

    st.markdown("### Custodians (Persons)")
    st.caption(
            "Add 1..N persons to be registered as dataset custodians.\n"
            "Priority order for matching: **Existing Person IRI** → **ORCID** → **First & Last name**.\n"
            "If you paste an IRI, it overrides ORCID and names.\n"
            "When no ORCID is given, and the Disambiguation toggle is ON, we search by family name and use\n"
            "fuzzy similarity on the given name to avoid duplicates."
        )

    n = st.number_input(
        "Number of custodians to add",
        min_value=0, max_value=20, value=0, step=1, key="cust_n"
    )

    st.markdown("### Disambiguation (avoid duplicates)")
    resolve_flag = st.checkbox(
        "Try to match custodian Persons in EBRAINS (fairgraph)",
        value=False,
        help="If enabled, we will attempt to find existing Person entries in the KG before creating new ones."
    )
    resolve_token = st.text_input(
        "EBRAINS token for disambiguation (optional)",
        type="password",
        value=os.getenv("EBRAINS_TOKEN", "")
    )

    with st.form("patch_form"):
        answers = {}

        if "DatasetVersion.license" in prompts:
            lic_labels = ["(choose)"] + sorted(LICENSE.keys()) + ["Enter IRI manually"]
            lic_choice = st.selectbox(
                "DatasetVersion.license", lic_labels, index=0, key="dv_license",
                help="Pick an openMINDS License or paste a full IRI."
            )
            if lic_choice == "Enter IRI manually":
                val = _check_iri_field(
                    "License IRI",
                    key="dv_license_iri",
                    placeholder="https://openminds.ebrains.eu/instances/licenses/CC-BY-4.0",
                )
                if val:
                    answers["DatasetVersion.license"] = val

        if "DatasetVersion.accessibility" in prompts:
            acc_labels = ["(choose)"] + sorted(ACCESSIBILITY.keys()) + ["Enter IRI manually"]
            acc_choice = st.selectbox(
                "DatasetVersion.accessibility", acc_labels, index=0, key="dv_access",
                help="Pick an openMINDS ProductAccessibility or paste a full IRI."
            )
            if acc_choice == "Enter IRI manually":
                val = _check_iri_field(
                    "Accessibility IRI",
                    key="dv_access_iri",
                    placeholder="https://openminds.ebrains.eu/instances/productAccessibility/freeAccess",
                )
                if val:
                    answers["DatasetVersion.accessibility"] = val

        if "SubjectState.ageCategory" in prompts or "SubjectGroupState.ageCategory" in prompts:
            age_labels = ["(choose)"] + sorted(AGE_CATEGORY.keys()) + ["Enter IRI manually"]
            age_choice = st.selectbox(
                "AgeCategory (SubjectState / SubjectGroupState)",
                age_labels, index=0, key="ss_age",
                help="Pick an openMINDS AgeCategory or paste a full IRI."
            )
            if age_choice == "Enter IRI manually":
                val = _check_iri_field(
                    "AgeCategory IRI",
                    key="ss_age_iri",
                    placeholder="https://openminds.ebrains.eu/instances/ageCategory/youngAdult",
                )
                if val:
                    answers["SubjectState.ageCategory"] = val
                    answers["SubjectGroupState.ageCategory"] = val

        v = _maybe_text("DatasetVersion.versionIdentifier", "DatasetVersion.versionIdentifier", "v1.0.0", "Short identifier for this dataset version.")
        if v: answers["DatasetVersion.versionIdentifier"] = v
        v = _maybe_text("Dataset.description", "Dataset.description", "One-paragraph dataset description.", "Human-readable dataset description.")
        if v: answers["Dataset.description"] = v
        v = _maybe_text("DatasetVersion.fullDocumentation", "DatasetVersion.fullDocumentation", "URL or note (e.g., see README).", "Where full documentation can be found.")
        if v: answers["DatasetVersion.fullDocumentation"] = v
        v = _maybe_text("DatasetVersion.preparationDesign", "DatasetVersion.preparationDesign", "Converted from BIDS using bids2openminds.", "How the data were prepared or converted.")
        if v: answers["DatasetVersion.preparationDesign"] = v
        v = _maybe_text("DatasetVersion.ethicsAssessment", "DatasetVersion.ethicsAssessment", "De-identified; IRB approved.", "Brief ethics/compliance statement.")
        if v: answers["DatasetVersion.ethicsAssessment"] = v
        v = _maybe_text("DatasetVersion.studyTarget", "DatasetVersion.studyTarget", "Human risk-taking behavior; fMRI.", "Primary study target of the dataset.")
        if v: answers["DatasetVersion.studyTarget"] = v
        v = _maybe_text("DatasetVersion.keyword", "DatasetVersion.keyword", "fMRI; risk-taking; neuroimaging", "Keywords; use semicolons to separate multiple terms.")
        if v: answers["DatasetVersion.keyword"] = v

        custodians = []
        for i in range(int(n)):
            with st.container():
                cols = st.columns([3.3, 1.7, 1.5, 1.5])

                iri = cols[0].text_input(
                    f"Existing Person IRI #{i+1} (highest priority)",
                    placeholder="https://kg.ebrains.eu/api/instances/<uuid>",
                    key=f"cust_iri_{i}",
                    help="If provided, we will link this exact Person and ignore ORCID/names."
                )
                orcid = cols[1].text_input(
                    f"ORCID #{i+1}",
                    placeholder="0000-0002-1825-0097",
                    key=f"cust_orcid_{i}",
                    help="If IRI is not provided, we match by ORCID (exact) if present."
                )
                first = cols[2].text_input(
                    f"First name #{i+1}",
                    key=f"cust_first_{i}",
                    help="Used only if IRI is empty and ORCID not provided."
                )
                last = cols[3].text_input(
                    f"Last name #{i+1}",
                    key=f"cust_last_{i}",
                    help="Used only if IRI is empty and ORCID not provided."
                )

                if iri.strip():
                    custodians.append(iri.strip())
                else:
                    spec = {}
                    if orcid.strip():
                        spec["orcid"] = orcid.strip()
                    if first.strip():
                        spec["first"] = first.strip()
                    if last.strip():
                        spec["last"]  = last.strip()

                    if spec.get("orcid") or (spec.get("first") and spec.get("last")):
                        custodians.append(spec)

        if custodians:
            answers["custodians"] = custodians

        submitted = st.form_submit_button("Patch", help="Apply provided values to all missing fields.")
        if submitted:
            if not answers:
                st.warning("Please enter at least one value before patching.")
            else:
                patch_openminds(
                    Path(jsonld),
                    repo_iri="",
                    interactive=False,
                    answers=answers,
                    resolve_persons=resolve_flag,
                    token=resolve_token or None,
                )
                st.success("Patched missing fields in JSON-LD files.")
                errs = validate_jsonld(Path(jsonld))
                if not errs:
                    st.success("Schema validation passed")
                else:
                    st.error(f"Schema validation found {len(errs)} issue(s):")
                    for fp, msg in errs[:50]:
                        st.write(f"• **{fp}** — {msg}")
                    st.info("Fix the inputs above and patch again, or correct the JSON-LD manually.")

    if st.button("Validate JSON-LD"):
        errs = validate_jsonld(Path(jsonld))
        if not errs:
            st.success("Schema validation passed")
        else:
            st.error(f"Schema validation found {len(errs)} issue(s):")
            for fp, msg in errs[:100]:
                st.write(f"• **{fp}** — {msg}")

# Step 3 Upload
with st.expander("Step 3 Upload 🚀"):
    jsonld = st.text_input(
        "JSON-LD folder to upload",
        "openminds-out",
        help="Folder containing the .jsonld files to upload."
    )
    space = st.text_input(
        "KG space",
        "collab-bids2ebrains-test",
        help="Target EBRAINS KG space."
    )
    token = st.text_input(
        "EBRAINS token (or set EBRAINS_TOKEN env)",
        type="password",
        value=os.getenv("EBRAINS_TOKEN", ""),
        help="Personal access token from the EBRAINS portal."
    )

    if st.button("Upload"):
        errs = validate_jsonld(Path(jsonld))
        if errs:
            st.error("Upload blocked: schema validation failed. Please fix errors before uploading.")
            for fp, msg in errs[:50]:
                st.write(f"• **{fp}** — {msg}")
        else:
            with st.status("Uploading to EBRAINS KG…", expanded=True) as status:
                upload_to_kg(Path(jsonld), space=space, token=token or None)
                status.update(label="Upload completed successfully.", state="complete", expanded=False)
            st.balloons()
