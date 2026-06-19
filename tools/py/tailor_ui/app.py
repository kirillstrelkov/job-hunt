"""Streamlit user interface for CV tailoring, editing, checking and PDF conversion."""

import argparse
import base64
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import yaml
from loguru import logger

# Add required paths
tools_py_dir = Path(__file__).resolve().parent.parent
cv_tools_dir = tools_py_dir.parent.parent / "cv" / "tools"

if str(tools_py_dir) not in sys.path:
    sys.path.insert(0, str(tools_py_dir))
if str(cv_tools_dir) not in sys.path:
    sys.path.insert(0, str(cv_tools_dir))


def generate_config(output_path: str) -> None:
    """Generate consolidated configuration file from CV and helper configs."""
    logger.info(f"Generating consolidated config at {output_path}")

    cv_config_path = cv_tools_dir.parent / "tmp" / "config.yml"
    helpers_config_path = tools_py_dir / "helpers" / "config.yaml"

    consolidated = {}

    # Read CV config
    if cv_config_path.exists():
        with cv_config_path.open(encoding="utf-8") as f:
            cv_config = yaml.safe_load(f)
            if cv_config:
                # Resolve paths relative to cv/tmp
                for k, v in cv_config.items():
                    if isinstance(v, str):
                        p = Path(v)
                        if not p.is_absolute():
                            cv_config[k] = str((cv_config_path.parent / p).resolve())
                consolidated.update(cv_config)
    else:
        logger.warning(f"Warning: {cv_config_path} not found.")

    # Read Helpers config
    if helpers_config_path.exists():
        with helpers_config_path.open(encoding="utf-8") as f:
            helpers_config = yaml.safe_load(f)
            if helpers_config:
                consolidated["ollama"] = {
                    "eval_model": helpers_config.get("eval_model"),
                    "models": helpers_config.get("models"),
                    "model_default_options": helpers_config.get("model_default_options"),
                }
    else:
        logger.warning(f"Warning: {helpers_config_path} not found.")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(consolidated, f, default_flow_style=False, sort_keys=False)

    logger.info("Done!")


def main_cli() -> None:
    """Parse command line arguments and execute CLI operations."""
    parser = argparse.ArgumentParser(description="Tailored CV UI / CLI")
    parser.add_argument(
        "--generate-config", type=str, nargs="?", const="./config.yaml", help="Generate a consolidated config file"
    )

    # If run under streamlit, sys.argv will have 'streamlit run ...'
    # We only parse args if we are clearly running as python script
    if "--generate-config" in sys.argv:
        args, _ = parser.parse_known_args()
        if args.generate_config:
            generate_config(args.generate_config)
            sys.exit(0)


main_cli()

try:
    import streamlit as st
except ImportError:
    logger.error("Streamlit is not installed. Please install it using `uv add streamlit`.")
    sys.exit(1)

import process_cv  # noqa: E402

from helpers.ollama_helper import run_model  # noqa: E402


def compile_pdf(md_path: str, pdf_path: str) -> None:
    """Compile Markdown file to PDF using pandoc."""
    pandoc_path = shutil.which("pandoc") or "pandoc"
    try:
        subprocess.run(  # noqa: S603
            [
                pandoc_path,
                "--pdf-engine=xelatex",
                "-V",
                "papersize=a4",
                "-V",
                "geometry:margin=1.5cm",
                md_path,
                "-o",
                pdf_path,
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning(f"xelatex failed, falling back to default pdf engine: {e}")
        subprocess.run(  # noqa: S603
            [pandoc_path, "-V", "papersize=a4", "-V", "geometry:margin=1.5cm", md_path, "-o", pdf_path], check=True
        )


def get_temp_generation_dir() -> Path:
    """Create and return a new timestamped temporary directory for file operations."""
    dt_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir()) / "tmp_tailor_cv" / f"{dt_str}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def run_check_on_text(md_content: str) -> list[str]:
    """Execute validation checks on the given markdown resume text."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(md_content)
        temp_path = temp_file.name
    try:
        sections = process_cv.split_into_sections(temp_path)
        errors = process_cv.do_check(sections)
        return [f"Line {err.line_num}: {err.msg} (content: `{err.line}`)" for err in errors]
    finally:
        with contextlib.suppress(Exception):
            Path(temp_path).unlink()


st.set_page_config(layout="wide", page_title="Tailored CV UI")
st.title("Tailored CV UI")

# Premium styling for primary CTA buttons to be blue
st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button[kind="primary"]:active {
        transform: translateY(0px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_unified_config(path: str) -> dict:
    """Load and parse the consolidated YAML config file."""
    p = Path(path)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Initial Config Loading
if "config" not in st.session_state:
    config_path = st.session_state.get("config_path_input_val", "./config.yaml")
    if Path(config_path).exists():
        st.session_state["config"] = load_unified_config(config_path)
    else:
        st.session_state["config"] = {}

if "local_llm_stdout" not in st.session_state:
    st.session_state["local_llm_stdout"] = ""

if "shared_jd" not in st.session_state:
    st.session_state["shared_jd"] = ""
if "jd_local" not in st.session_state:
    st.session_state["jd_local"] = ""
if "jd_manual" not in st.session_state:
    st.session_state["jd_manual"] = ""


def on_jd_local_change() -> None:
    """Sync the local tab JD with the shared session state JD."""
    st.session_state["shared_jd"] = st.session_state["jd_local"]


def on_jd_manual_change() -> None:
    """Sync the manual tab JD with the shared session state JD."""
    st.session_state["shared_jd"] = st.session_state["jd_manual"]


cfg = st.session_state["config"]


def read_file(path: str | Path | None) -> str:
    """Read and return string content of a file path."""
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    with p.open(encoding="utf-8") as f:
        return f.read()


# Load master texts
if "master_texts" not in st.session_state:
    st.session_state["master_texts"] = {
        "header": read_file(cfg.get("header")),
        "body": read_file(cfg.get("body")),
        "footer": read_file(cfg.get("footer")),
        "prompt": read_file(cfg.get("prompt")),
    }

models = []
if "ollama" in cfg and "models" in cfg["ollama"]:
    models = sorted([m["name"] for m in cfg["ollama"]["models"]])
eval_model = cfg.get("ollama", {}).get("eval_model", "")

# Main layout
tabs = st.tabs(["Tailor with local LLM", "Tailor manually", "MD to PDF Converter", "Configuration / Master Data"])

with tabs[0]:
    # 1. Expandable/Collapsible Local LLM Settings
    with st.expander("Local LLM Settings", expanded=False):
        selected_model = st.selectbox(
            "Ollama Model", options=models, index=models.index(eval_model) if eval_model in models else 0
        )
        # Resolve default values for the selected model from config
        model_opts = {}
        if "ollama" in cfg:
            for m in cfg["ollama"].get("models", []):
                if m["name"] == selected_model:
                    model_opts = m.get("options", {}).copy()
                    break
            default_opts = cfg["ollama"].get("model_default_options", {})
            resolved_opts = default_opts.copy()
            resolved_opts.update(model_opts)
        else:
            resolved_opts = {}

        init_num_ctx = resolved_opts.get("num_ctx", 16384)
        init_num_predict = resolved_opts.get("num_predict", -1)
        init_temp = resolved_opts.get("temperature", 0.1)
        init_repeat_penalty = resolved_opts.get("repeat_penalty", 1.1)

        col_opts1, col_opts2 = st.columns([1, 1])
        with col_opts1:
            num_ctx = st.number_input(
                "Context Window (num_ctx)",
                min_value=1024,
                max_value=128000,
                value=int(init_num_ctx),
                step=1024,
                key=f"num_ctx_{selected_model}",
            )
            num_predict = st.number_input(
                "Max Tokens (num_predict)",
                min_value=-2,
                max_value=32768,
                value=int(init_num_predict),
                step=1,
                key=f"num_predict_{selected_model}",
            )
        with col_opts2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=float(init_temp),
                step=0.01,
                key=f"temperature_{selected_model}",
            )
            repeat_penalty = st.slider(
                "Repeat Penalty (repeat_penalty)",
                min_value=0.5,
                max_value=2.0,
                value=float(init_repeat_penalty),
                step=0.01,
                key=f"repeat_penalty_{selected_model}",
            )

        st.text_area(
            "Log Output",
            value=st.session_state.get("local_llm_stdout", ""),
            height=150,
            disabled=True,
        )

    st.subheader("Step 1: Enter Job Description")
    with st.expander("Show/Hide Job Description", expanded=True):
        jd_local = st.text_area(
            "Paste JD here", height=250, key="jd_local", label_visibility="collapsed", on_change=on_jd_local_change
        )

    # 3. Dynamic column structure for CV Markdown and CV PDF
    show_pdf_local = st.session_state.get("show_pdf_local_val", True)

    if show_pdf_local:
        col_md, col_pdf = st.columns([1, 1])
    else:
        col_md = st.container()

    with col_md:
        st.subheader("Step 2: Tailor CV to Markdown")

        # Combine CV
        tailored_body = st.session_state.get("tailored_body", "")
        if not tailored_body:
            full_cv_md = ""
        else:
            header = st.session_state["master_texts"]["header"]
            footer = st.session_state["master_texts"]["footer"]
            full_cv_md = f"{header}\n\n{tailored_body}\n\n{footer}"

        # Apply any pending update from PDF handler (must happen before widget is rendered)
        if "_edited_cv_local_pending" in st.session_state:
            st.session_state["edited_cv_local"] = st.session_state.pop("_edited_cv_local_pending")

        if "edited_cv_local" not in st.session_state:
            st.session_state["edited_cv_local"] = full_cv_md

        edited_full_cv = st.session_state.get("edited_cv_local", full_cv_md)

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            btn_gen_local_clicked = st.button(
                "Tailor CV with Local LLM", use_container_width=True, key="btn_gen_local", type="primary"
            )
        with col_btn2:
            btn_check_local_clicked = st.button(
                "Check CV", use_container_width=True, key="btn_check_local", type="secondary"
            )
        with col_btn3:
            st.download_button(
                "Save Tailored CV as Markdown",
                edited_full_cv,
                file_name="cv.md",
                key="dl_md_local",
                use_container_width=True,
            )

        # Message placeholders directly after buttons
        if st.session_state.get("local_tailor_error"):
            st.error(st.session_state["local_tailor_error"])
        if st.session_state.get("local_tailor_warning"):
            st.warning(st.session_state["local_tailor_warning"])
        if st.session_state.get("local_tailor_note"):
            st.info(st.session_state["local_tailor_note"])

        if btn_check_local_clicked:
            st.session_state.pop("local_tailor_error", None)
            st.session_state.pop("local_tailor_warning", None)
            st.session_state.pop("local_tailor_note", None)
            if not edited_full_cv.strip():
                st.session_state["local_tailor_warning"] = "No CV text to check."
                st.rerun()
            else:
                errors = run_check_on_text(edited_full_cv)
                st.session_state["local_cv_errors"] = errors
                st.session_state["local_cv_checked"] = True
                if errors:
                    st.session_state["local_tailor_error"] = (
                        f"CV check failed with {len(errors)} errors:\n" + "\n".join([f"- {err}" for err in errors])
                    )
                else:
                    st.session_state["local_tailor_note"] = "No CV errors found!"
                st.rerun()

        if btn_gen_local_clicked:
            st.session_state.pop("local_tailor_error", None)
            st.session_state.pop("local_tailor_warning", None)
            st.session_state.pop("local_tailor_note", None)
            if not jd_local.strip():
                st.session_state["local_tailor_warning"] = "Please paste a Job Description first."
                st.rerun()
            else:
                st.session_state["local_llm_stdout"] = "Tailoring...\n"
                prompt_template = st.session_state["master_texts"]["prompt"]
                master_cv = st.session_state["master_texts"]["body"]
                hydrated = prompt_template.format(master_cv=master_cv, job_description=jd_local)

                with st.spinner(f"Running Ollama ({selected_model})..."):
                    try:
                        # Extract options for selected model
                        options = {}
                        for m in cfg.get("ollama", {}).get("models", []):
                            if m["name"] == selected_model:
                                options = m.get("options", {})
                                break

                        default_opts = cfg.get("ollama", {}).get("model_default_options", {})
                        opts = default_opts.copy()
                        opts.update(options)

                        # Overwrite with overrides
                        opts["num_ctx"] = num_ctx
                        opts["num_predict"] = num_predict
                        opts["temperature"] = temperature
                        opts["repeat_penalty"] = repeat_penalty

                        f_out = io.StringIO()
                        handler_id = logger.add(f_out, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

                        try:
                            with contextlib.redirect_stdout(f_out), contextlib.redirect_stderr(f_out):
                                result = run_model(model=selected_model, prompt_content=hydrated, options=opts)
                        finally:
                            logger.remove(handler_id)
                            st.session_state["local_llm_stdout"] = f_out.getvalue()

                        response_text = result.get("response", "")

                        # Process output to trim to CV
                        lines = response_text.splitlines()
                        start_idx = 0
                        for i, line in enumerate(lines):
                            if "Summary" in line:
                                start_idx = i
                                break
                        end_idx = len(lines)
                        for i in range(start_idx, len(lines)):
                            if "TAILORING JUSTIFICATION REPORT" in lines[i]:
                                end_idx = i
                                break
                        trimmed_text = "\n".join(lines[start_idx:end_idx]).strip()

                        st.session_state["tailored_body"] = trimmed_text
                        # Fix the assembled CV and display the fixed version
                        header = st.session_state["master_texts"]["header"]
                        footer = st.session_state["master_texts"]["footer"]
                        full_cv_md = f"{header}\n\n{trimmed_text}\n\n{footer}"
                        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as _tf:
                            _tf.write(full_cv_md)
                            _tf_path = _tf.name
                        try:
                            process_cv.fix_file(_tf_path)
                            with Path(_tf_path).open(encoding="utf-8") as _tf:
                                full_cv_md = _tf.read()
                        finally:
                            with contextlib.suppress(Exception):
                                Path(_tf_path).unlink()
                        st.session_state["edited_cv_local"] = full_cv_md
                        st.session_state.pop("pdf_bytes", None)
                        st.session_state.pop("local_cv_errors", None)
                        st.session_state.pop("local_cv_checked", None)
                        st.session_state["local_tailor_note"] = "CV Tailored successfully!"
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.session_state["local_tailor_error"] = f"LLM Generation Failed: {e}"
                        st.rerun()

        st.toggle("Show PDF Preview", value=st.session_state.get("show_pdf_local_val", True), key="show_pdf_local_val")

        cv_edit_tab, cv_preview_tab = st.tabs(["Edit", "Preview"])
        with cv_edit_tab:
            st.text_area("Full CV Markdown text", height=600, key="edited_cv_local", label_visibility="collapsed")
        with cv_preview_tab:
            st.markdown(st.session_state.get("edited_cv_local", full_cv_md))

    if show_pdf_local:
        with col_pdf:
            st.subheader("Step 3: Convert CV to PDF")

            col_pdf_btns1, col_pdf_btns2 = st.columns([1, 1])
            with col_pdf_btns1:
                btn_pdf_local_clicked = st.button(
                    "Convert Markdown CV to PDF",
                    use_container_width=True,
                    key="btn_pdf_local",
                    disabled=not edited_full_cv.strip(),
                    type="primary",
                )
            with col_pdf_btns2:
                if "pdf_bytes" in st.session_state:
                    st.download_button(
                        "Save Tailored CV as PDF",
                        st.session_state["pdf_bytes"],
                        file_name="cv.pdf",
                        key="dl_pdf_local",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "Save Tailored CV as PDF", disabled=True, use_container_width=True, key="dl_pdf_local_disabled"
                    )

            # Message placeholders directly after buttons
            if st.session_state.get("local_pdf_error"):
                st.error(st.session_state["local_pdf_error"])
            if st.session_state.get("local_pdf_warning"):
                st.warning(st.session_state["local_pdf_warning"])
            if st.session_state.get("local_pdf_note"):
                st.info(st.session_state["local_pdf_note"])

            if btn_pdf_local_clicked:
                st.session_state.pop("local_pdf_error", None)
                st.session_state.pop("local_pdf_warning", None)
                st.session_state.pop("local_pdf_note", None)
                with st.spinner("Generating PDF..."):
                    run_dir = get_temp_generation_dir()
                    f_md_name = str(run_dir / "cv.md")
                    pdf_name = str(run_dir / "cv.pdf")

                    try:
                        with Path(f_md_name).open("w", encoding="utf-8") as f_md:
                            f_md.write(edited_full_cv)

                        # Convert to PDF
                        compile_pdf(f_md_name, pdf_name)

                        with Path(pdf_name).open("rb") as f_pdf:
                            st.session_state["pdf_bytes"] = f_pdf.read()
                        st.session_state["local_pdf_note"] = f"PDF Generated and stored at {pdf_name}!"
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.session_state["local_pdf_error"] = f"PDF generation failed: {e}"
                        st.rerun()

            if "pdf_bytes" in st.session_state:
                # Display PDF
                base64_pdf = base64.b64encode(st.session_state["pdf_bytes"]).decode("utf-8")
                iframe_style = 'width="100%" height="800" type="application/pdf"'
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" {iframe_style}></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.info("Click 'Convert Markdown CV to PDF' to preview.")

with tabs[1]:
    # Step 1: Enter Job Description
    st.subheader("Step 1: Enter Job Description")
    with st.expander("Show/Hide Job Description", expanded=True):
        jd_manual = st.text_area(
            "Paste JD here", height=300, key="jd_manual", label_visibility="collapsed", on_change=on_jd_manual_change
        )

    # Step 2: Generate Prompt for LLM
    st.subheader("Step 2: Generate Prompt for LLM")
    if st.button("Generate Prompt for LLM", key="btn_gen_prompt_manual", type="primary"):
        prompt_template = st.session_state["master_texts"]["prompt"]
        master_cv = st.session_state["master_texts"]["body"]
        try:
            hydrated = prompt_template.format(master_cv=master_cv, job_description=jd_manual)
            st.session_state["hydrated_prompt"] = hydrated
        except Exception as e:  # noqa: BLE001
            st.error(f"Error formatting prompt: {e}")

    if "hydrated_prompt" in st.session_state:
        st.text_area(
            "Hydrated Prompt (Ready for Online LLM)",
            value=st.session_state["hydrated_prompt"],
            height=200,
            key="hydrated_prompt_manual_view",
        )

    # Step 3: Enter Tailored body
    st.subheader("Step 3: Enter Tailored body")
    manual_body = st.text_area("Manual Tailored Body (Paste from Online LLM)", height=200, key="manual_body_input")

    # Combine CV
    tailored_body = st.session_state.get("tailored_body", "")
    if not tailored_body:
        full_cv_md = ""
    else:
        header = st.session_state["master_texts"]["header"]
        footer = st.session_state["master_texts"]["footer"]
        full_cv_md = f"{header}\n\n{tailored_body}\n\n{footer}"

    # Apply any pending update from PDF handler (must happen before widget is rendered)
    if "_edited_cv_manual_pending" in st.session_state:
        st.session_state["edited_cv_manual"] = st.session_state.pop("_edited_cv_manual_pending")

    if "edited_cv_manual" not in st.session_state:
        st.session_state["edited_cv_manual"] = full_cv_md

    edited_full_cv = st.session_state.get("edited_cv_manual", full_cv_md)

    # Dynamic column structure for Step 4 (Markdown) and Step 5 (PDF)
    show_pdf_manual = st.session_state.get("show_pdf_manual_val", True)

    if show_pdf_manual:
        col_md_man, col_pdf_man = st.columns([1, 1])
    else:
        col_md_man = st.container()

    with col_md_man:
        st.subheader("Step 4: Tailor CV to Markdown")
        st.toggle(
            "Show PDF Preview", value=st.session_state.get("show_pdf_manual_val", True), key="show_pdf_manual_val"
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            btn_use_manual = st.button(
                "Tailor CV manually", key="btn_use_manual_body", type="primary", use_container_width=True
            )
        with col_btn2:
            btn_check_manual_clicked = st.button(
                "Check CV", use_container_width=True, key="btn_check_manual", type="secondary"
            )
        with col_btn3:
            st.download_button(
                "Save Tailored CV as Markdown",
                edited_full_cv,
                file_name="cv.md",
                key="dl_md_manual",
                use_container_width=True,
            )

        # Message placeholders directly after buttons
        if st.session_state.get("manual_tailor_error"):
            st.error(st.session_state["manual_tailor_error"])
        if st.session_state.get("manual_tailor_warning"):
            st.warning(st.session_state["manual_tailor_warning"])
        if st.session_state.get("manual_tailor_note"):
            st.info(st.session_state["manual_tailor_note"])

        if btn_check_manual_clicked:
            st.session_state.pop("manual_tailor_error", None)
            st.session_state.pop("manual_tailor_warning", None)
            st.session_state.pop("manual_tailor_note", None)
            if not edited_full_cv.strip():
                st.session_state["manual_tailor_warning"] = "No CV text to check."
                st.rerun()
            else:
                errors = run_check_on_text(edited_full_cv)
                st.session_state["manual_cv_errors"] = errors
                st.session_state["manual_cv_checked"] = True
                if errors:
                    st.session_state["manual_tailor_error"] = (
                        f"CV check failed with {len(errors)} errors:\n" + "\n".join([f"- {err}" for err in errors])
                    )
                else:
                    st.session_state["manual_tailor_note"] = "No CV errors found!"
                st.rerun()

        if btn_use_manual:
            st.session_state.pop("manual_tailor_error", None)
            st.session_state.pop("manual_tailor_warning", None)
            st.session_state.pop("manual_tailor_note", None)
            if not manual_body.strip():
                st.session_state["manual_tailor_warning"] = "Please paste the manual tailored body from Step 3 first."
                st.rerun()
            else:
                st.session_state["tailored_body"] = manual_body
                header = st.session_state["master_texts"]["header"]
                footer = st.session_state["master_texts"]["footer"]
                full_cv_md = f"{header}\n\n{manual_body}\n\n{footer}"
                with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as _tf:
                    _tf.write(full_cv_md)
                    _tf_path = _tf.name
                try:
                    process_cv.fix_file(_tf_path)
                    with Path(_tf_path).open(encoding="utf-8") as _tf:
                        full_cv_md = _tf.read()
                finally:
                    with contextlib.suppress(Exception):
                        Path(_tf_path).unlink()
                st.session_state["edited_cv_manual"] = full_cv_md
                st.session_state.pop("pdf_bytes", None)
                st.session_state.pop("manual_cv_errors", None)
                st.session_state.pop("manual_cv_checked", None)
                st.session_state["manual_tailor_note"] = "CV Tailored manually successfully!"
                st.rerun()

        cv_edit_tab, cv_preview_tab = st.tabs(["Edit", "Preview"])
        with cv_edit_tab:
            st.text_area("Full CV Markdown text", height=600, key="edited_cv_manual", label_visibility="collapsed")
        with cv_preview_tab:
            st.markdown(st.session_state.get("edited_cv_manual", full_cv_md))

    if show_pdf_manual:
        with col_pdf_man:
            st.subheader("Step 5: Convert CV to PDF")

            col_pdf_btns1, col_pdf_btns2 = st.columns([1, 1])
            with col_pdf_btns1:
                btn_pdf_manual_clicked = st.button(
                    "Convert Markdown CV to PDF",
                    use_container_width=True,
                    key="btn_pdf_manual",
                    disabled=not edited_full_cv.strip(),
                    type="primary",
                )
            with col_pdf_btns2:
                if "pdf_bytes" in st.session_state:
                    st.download_button(
                        "Save Tailored CV as PDF",
                        st.session_state["pdf_bytes"],
                        file_name="cv.pdf",
                        key="dl_pdf_manual",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "Save Tailored CV as PDF", disabled=True, use_container_width=True, key="dl_pdf_manual_disabled"
                    )

            # Message placeholders directly after buttons
            if st.session_state.get("manual_pdf_error"):
                st.error(st.session_state["manual_pdf_error"])
            if st.session_state.get("manual_pdf_warning"):
                st.warning(st.session_state["manual_pdf_warning"])
            if st.session_state.get("manual_pdf_note"):
                st.info(st.session_state["manual_pdf_note"])

            if btn_pdf_manual_clicked:
                st.session_state.pop("manual_pdf_error", None)
                st.session_state.pop("manual_pdf_warning", None)
                st.session_state.pop("manual_pdf_note", None)
                with st.spinner("Generating PDF..."):
                    run_dir = get_temp_generation_dir()
                    f_md_name = str(run_dir / "cv.md")
                    pdf_name = str(run_dir / "cv.pdf")

                    try:
                        with Path(f_md_name).open("w", encoding="utf-8") as f_md:
                            f_md.write(edited_full_cv)

                        # Convert to PDF
                        compile_pdf(f_md_name, pdf_name)

                        with Path(pdf_name).open("rb") as f_pdf:
                            st.session_state["pdf_bytes"] = f_pdf.read()
                        st.session_state["manual_pdf_note"] = f"PDF Generated and stored at {pdf_name}!"
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.session_state["manual_pdf_error"] = f"PDF generation failed: {e}"
                        st.rerun()

            if "pdf_bytes" in st.session_state:
                # Display PDF
                base64_pdf = base64.b64encode(st.session_state["pdf_bytes"]).decode("utf-8")
                iframe_style = 'width="100%" height="800" type="application/pdf"'
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" {iframe_style}></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.info("Click 'Convert Markdown CV to PDF' to preview.")

with tabs[2]:
    st.header("MD to PDF Converter")
    col_md, col_pdf = st.columns([1, 1])
    with col_md:
        st.subheader("Markdown Input")
        arbitrary_edit_tab, arbitrary_preview_tab = st.tabs(["Edit", "Preview"])
        with arbitrary_edit_tab:
            arbitrary_md = st.text_area(
                "Paste any Markdown here", height=600, key="arbitrary_md", label_visibility="collapsed"
            )
        with arbitrary_preview_tab:
            st.markdown(st.session_state.get("arbitrary_md", ""))
        arbitrary_md = st.session_state.get("arbitrary_md", "")
    with col_pdf:
        st.subheader("PDF Output")
        btn_gen_arb_clicked = st.button(
            "Generate PDF", key="btn_gen_arbitrary_pdf", use_container_width=True, disabled=not arbitrary_md.strip()
        )
        if btn_gen_arb_clicked:
            with st.spinner("Generating PDF..."):
                run_dir = get_temp_generation_dir()
                f_md_name = str(run_dir / "document.md")
                pdf_name = str(run_dir / "document.pdf")

                try:
                    with Path(f_md_name).open("w", encoding="utf-8") as f_md:
                        f_md.write(arbitrary_md)

                    # Fix CV markdown using process_cv
                    process_cv.fix_file(f_md_name)

                    # Read back the fixed content to update the UI
                    with Path(f_md_name).open(encoding="utf-8") as f_md:
                        fixed_content = f_md.read()
                    st.session_state["arbitrary_md"] = fixed_content

                    # Convert to PDF
                    compile_pdf(f_md_name, pdf_name)

                    with Path(pdf_name).open("rb") as f_pdf:
                        st.session_state["arbitrary_pdf_bytes"] = f_pdf.read()
                    st.success(f"PDF Generated and stored at {pdf_name}!")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"PDF generation failed: {e}")

        if "arbitrary_pdf_bytes" in st.session_state:
            st.download_button(
                "Download PDF",
                st.session_state["arbitrary_pdf_bytes"],
                file_name="document.pdf",
                key="dl_arbitrary_pdf",
            )

            # Display PDF
            base64_pdf = base64.b64encode(st.session_state["arbitrary_pdf_bytes"]).decode("utf-8")
            iframe_style = 'width="100%" height="800" type="application/pdf"'
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" {iframe_style}></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.info("Click 'Generate PDF' to preview.")

with tabs[3]:
    st.header("Configuration")
    config_path_input = st.text_input(
        "Config File Path",
        value=st.session_state.get("config_path_input_val", "./config.yaml"),
        key="config_path_input_val",
    )
    if st.button("Load Config", key="btn_load_config_tabs"):
        st.session_state["config"] = load_unified_config(config_path_input)
        st.session_state.pop("master_texts", None)
        st.session_state.pop("edited_cv_local", None)
        st.session_state.pop("edited_cv_manual", None)
        st.session_state.pop("tailored_body", None)
        st.session_state.pop("shared_jd", None)
        st.session_state.pop("jd_local", None)
        st.session_state.pop("jd_manual", None)
        st.session_state.pop("pdf_bytes", None)
        st.session_state.pop("arbitrary_pdf_bytes", None)
        st.session_state.pop("local_cv_errors", None)
        st.session_state.pop("local_cv_checked", None)
        st.session_state.pop("manual_cv_errors", None)
        st.session_state.pop("manual_cv_checked", None)
        st.session_state.pop("local_tailor_error", None)
        st.session_state.pop("local_tailor_warning", None)
        st.session_state.pop("local_tailor_note", None)
        st.session_state.pop("local_pdf_error", None)
        st.session_state.pop("local_pdf_warning", None)
        st.session_state.pop("local_pdf_note", None)
        st.session_state.pop("manual_tailor_error", None)
        st.session_state.pop("manual_tailor_warning", None)
        st.session_state.pop("manual_tailor_note", None)
        st.session_state.pop("manual_pdf_error", None)
        st.session_state.pop("manual_pdf_warning", None)
        st.session_state.pop("manual_pdf_note", None)
        st.success("Config loaded!")
        st.rerun()

    st.header("Master Data")

    # Auto-save callbacks for master sections
    def _save_master_section(key: str, path_key: str) -> None:
        """Save the content of a master textarea to its file."""
        content = st.session_state.get(key, "")
        file_path = cfg.get(path_key)
        if file_path:
            try:
                with Path(file_path).open("w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Saved {key} to {file_path}")
                # Update in-memory master_texts dict
                st.session_state["master_texts"][path_key] = content
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to save {key} to {file_path}: {e}")

    # Header
    st.session_state["master_texts"]["header"] = st.text_area(
        "Header",
        value=st.session_state["master_texts"]["header"],
        height=200,
        key="master_header_editor",
        on_change=_save_master_section,
        args=("master_header_editor", "header"),
    )

    st.subheader("Master Body")
    body_edit_tab, body_preview_tab = st.tabs(["Edit", "Preview"])
    with body_edit_tab:
        st.session_state["master_texts"]["body"] = st.text_area(
            "Master Body text",
            value=st.session_state["master_texts"]["body"],
            height=400,
            label_visibility="collapsed",
            key="master_body_editor",
            on_change=_save_master_section,
            args=("master_body_editor", "body"),
        )
    with body_preview_tab:
        st.markdown(st.session_state["master_texts"]["body"])

    # Footer
    st.session_state["master_texts"]["footer"] = st.text_area(
        "Footer",
        value=st.session_state["master_texts"]["footer"],
        height=200,
        key="master_footer_editor",
        on_change=_save_master_section,
        args=("master_footer_editor", "footer"),
    )

    st.subheader("Prompt Template")
    prompt_edit_tab, prompt_preview_tab = st.tabs(["Edit", "Preview"])
    with prompt_edit_tab:
        st.session_state["master_texts"]["prompt"] = st.text_area(
            "Prompt Template text",
            value=st.session_state["master_texts"]["prompt"],
            height=300,
            label_visibility="collapsed",
            key="master_prompt_editor",
            on_change=_save_master_section,
            args=("master_prompt_editor", "prompt"),
        )
    with prompt_preview_tab:
        st.markdown(st.session_state["master_texts"]["prompt"])
