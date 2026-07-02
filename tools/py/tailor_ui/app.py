"""Streamlit user interface for CV tailoring, editing, checking and PDF conversion."""

import argparse
import base64
import contextlib
import hashlib
import importlib
import io
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st
import yaml
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from cv.tools import process_cv

importlib.reload(process_cv)
from cv.tools.md2pdf import convert_md_to_pdf
from helpers.llm_helper import get_model_names as get_gemini_models
from helpers.llm_helper import run_model as run_gemini_model
from helpers.ollama_helper import run_model as run_ollama_model

# Add required paths
tools_py_dir = Path(__file__).resolve().parent.parent
cv_tools_dir = tools_py_dir / "cv" / "tools"


def generate_config(output_path: str) -> None:
    """Generate consolidated configuration file from unified config.yaml."""
    logger.info(f"Generating consolidated config at {output_path}")

    unified_config_path = tools_py_dir / "config" / "config.yaml"
    consolidated = {}

    if unified_config_path.exists():
        with unified_config_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Flatten composer and tailor sections
        if "composer" in data:
            consolidated.update(data.get("composer") or {})
        if "tailor" in data:
            consolidated.update(data.get("tailor") or {})
        consolidated.update({k: v for k, v in data.items() if k not in ("composer", "tailor")})

        # Resolve relative paths relative to config/ folder
        config_dir = unified_config_path.parent
        for k, v in consolidated.items():
            if isinstance(v, str) and (v.startswith(("./", "../")) or v in {".", ".."}):
                consolidated[k] = str((config_dir / v).resolve())
    else:
        logger.warning(f"Warning: {unified_config_path} not found.")

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


# Load API Key from session state if stored
if st.session_state.get("gemini_api_key_val"):
    os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key_val"]


def compile_pdf(md_path: str, pdf_path: str) -> None:
    """Compile Markdown file to PDF using cv/tools/md2pdf.py."""
    try:
        convert_md_to_pdf(Path(md_path), Path(pdf_path))
    except SystemExit as e:
        if e.code != 0:
            msg = f"PDF generation failed with exit code {e.code}"
            raise RuntimeError(msg) from e


def get_temp_generation_dir(jd_text: str | None = None) -> tuple[Path, str]:
    """Create and return a temporary directory path and a timestamp string."""
    dt_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    if jd_text and jd_text.strip():
        jd_hash = hashlib.md5(jd_text.strip().encode("utf-8"), usedforsecurity=False).hexdigest()
        temp_dir = Path(tempfile.gettempdir()) / "tmp_compose_cv" / jd_hash
    else:
        temp_dir = Path(tempfile.gettempdir()) / "tmp_compose_cv" / "default"

    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir, dt_str


st.set_page_config(layout="wide", page_title="CV Composer")
st.title("CV Composer")

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
        data = yaml.safe_load(f) or {}

    # Extract composer and tailor settings to root level
    if "composer" in data:
        data.update(data.get("composer") or {})
    if "tailor" in data:
        data.update(data.get("tailor") or {})
    if "paths" in data:
        data.update(data.get("paths") or {})
    if "llm" in data:
        llm = data.get("llm") or {}
        data.update(llm)
        # Ensure eval_model, models and gemini_models are available at root level
        data["eval_model"] = llm.get("eval_mode")
        data["model_default_options"] = llm.get("model_default_options")
        data["top_models"] = llm.get("top_models")

        ollama_models = llm.get("ollama", {}).get("models", [])
        gemini_models = llm.get("gemini", {}).get("models", [])
        data["models"] = ollama_models + gemini_models
        data["gemini_models"] = [m["name"] for m in gemini_models]

        # Build "ollama" dictionary for UI compatibility
        data["ollama"] = {
            "eval_model": llm.get("eval_mode"),
            "model_default_options": llm.get("model_default_options"),
            "models": ollama_models,
            "top_models": llm.get("top_models"),
        }
    if "data" in data:
        data_sec = data.get("data") or {}
        if "jobs" in data_sec:
            data["jobs"] = data_sec["jobs"]

    # Resolve paths relative to config directory
    config_dir = p.parent
    for k, v in data.items():
        if isinstance(v, str) and (v.startswith(("./", "../")) or v in {".", ".."}):
            data[k] = str((config_dir / v).resolve())

    return data


def _clear_stale_config_states() -> None:
    """Clean up stale session state variables related to previous configuration."""
    st.session_state.pop("master_texts", None)
    st.session_state.pop("edited_cv_local", None)
    st.session_state.pop("edited_cv_manual", None)
    st.session_state.pop("_persistent_edited_cv_local", None)
    st.session_state.pop("_persistent_edited_cv_manual", None)
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


def load_config_action(path: str) -> None:
    """Load configuration and clean up stale state variables."""
    st.session_state["config"] = load_unified_config(path)
    _clear_stale_config_states()


def load_config_data_action(config_data: dict) -> None:
    """Load configuration data directly and clean up stale state variables."""
    st.session_state["config"] = config_data
    _clear_stale_config_states()


# Initial Config Loading
if "config" not in st.session_state:
    config_path = st.session_state.get("config_path_input_val", "../config/config.yaml")
    st.session_state["config"] = load_unified_config(config_path)

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


models = []
if "ollama" in cfg and "models" in cfg["ollama"]:
    models = sorted([m["name"] for m in cfg["ollama"]["models"]])
eval_model = cfg.get("ollama", {}).get("eval_model", "")

# Main layout
tabs = st.tabs(["Compose with LLM", "Compose manually", "MD to PDF Converter", "Settings"])

with tabs[0]:
    # Toggle between Local and Cloud LLM
    use_cloud = st.toggle(
        "Use Cloud LLM (Gemini)", value=st.session_state.get("use_cloud_llm", False), key="use_cloud_llm"
    )

    if use_cloud:
        # Cloud LLM Settings
        with st.expander("Cloud LLM (Gemini) Settings", expanded=False):
            gemini_models = list(get_gemini_models())
            selected_model = st.selectbox(
                "Gemini Model",
                options=gemini_models,
                index=0 if gemini_models else None,
                key="gemini_model_selectbox",
            )
            if not selected_model:
                selected_model = "gemini-2.5-flash"
            model_key_suffix = selected_model

            if not os.environ.get("GEMINI_API_KEY"):
                st.warning("⚠️ GEMINI_API_KEY is not set. Please set it in the 'Configuration / Master Data' tab.")

            init_max_tokens = 10240
            init_temp = 0.1
            init_seed = 42

            col_opts1, col_opts2 = st.columns([1, 1])
            with col_opts1:
                max_tokens = st.number_input(
                    "Max Tokens (max_tokens)",
                    min_value=1,
                    max_value=128000,
                    value=int(init_max_tokens),
                    step=1024,
                    key=f"max_tokens_{model_key_suffix}",
                )
                seed = st.number_input(
                    "Seed",
                    value=int(init_seed),
                    key=f"seed_{model_key_suffix}",
                )
            with col_opts2:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(init_temp),
                    step=0.01,
                    key=f"temperature_{model_key_suffix}",
                )
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=1,
                    max_value=1200,
                    value=600,
                    step=10,
                    key=f"timeout_{model_key_suffix}",
                )

            st.text_area(
                "Log Output",
                value=st.session_state.get("local_llm_stdout", ""),
                height=150,
                disabled=True,
            )
    else:
        # Local LLM Settings
        with st.expander("Local LLM (Ollama) Settings", expanded=False):
            models_list = list(models)
            selected_model = st.selectbox(
                "Ollama Model",
                options=models_list,
                index=models_list.index(eval_model) if eval_model in models_list else (0 if models_list else None),
                key="ollama_model_selectbox",
            )
            if not selected_model:
                selected_model = eval_model or "llama3"
            model_key_suffix = selected_model

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
                    key=f"num_ctx_{model_key_suffix}",
                )
                num_predict = st.number_input(
                    "Max Tokens (num_predict)",
                    min_value=-2,
                    max_value=32768,
                    value=int(init_num_predict),
                    step=1,
                    key=f"num_predict_{model_key_suffix}",
                )
            with col_opts2:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(init_temp),
                    step=0.01,
                    key=f"temperature_{model_key_suffix}",
                )
                repeat_penalty = st.slider(
                    "Repeat Penalty (repeat_penalty)",
                    min_value=0.5,
                    max_value=2.0,
                    value=float(init_repeat_penalty),
                    step=0.01,
                    key=f"repeat_penalty_{model_key_suffix}",
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
        st.subheader("Step 2: Compose CV to Markdown")

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
            st.session_state["edited_cv_local"] = st.session_state.get("_persistent_edited_cv_local", full_cv_md)

        edited_full_cv = st.session_state.get("edited_cv_local", full_cv_md)
        if "edited_cv_local" in st.session_state:
            st.session_state["_persistent_edited_cv_local"] = st.session_state["edited_cv_local"]

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            btn_gen_local_clicked = st.button(
                "Compose CV with LLM", use_container_width=True, key="btn_gen_local", type="primary"
            )
        with col_btn2:
            btn_check_local_clicked = st.button(
                "Check CV", use_container_width=True, key="btn_check_local", type="secondary"
            )
        with col_btn3:
            st.download_button(
                "Save Composed CV as Markdown",
                edited_full_cv,
                file_name="cv.md",
                key="dl_md_local",
                use_container_width=True,
            )

        fix_markdown = st.checkbox("Fix Markdown", value=True, key="fix_markdown_local")

        if btn_check_local_clicked:
            st.session_state.pop("local_tailor_error", None)
            st.session_state.pop("local_tailor_warning", None)
            st.session_state.pop("local_tailor_note", None)
            if not edited_full_cv.strip():
                st.session_state["local_tailor_warning"] = "No CV text to check."
                st.rerun()
            else:
                errors = process_cv.check_markdown(edited_full_cv)
                st.session_state["local_cv_checked"] = True
                if errors:
                    st.session_state["local_tailor_error"] = (
                        f"CV check failed with {len(errors)} errors:\n"
                        + "\n".join(f"- Line {err.line_num}: {err.msg} (content: `{err.line}`)" for err in errors)
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
            elif use_cloud and not os.environ.get("GEMINI_API_KEY"):
                st.session_state["local_tailor_error"] = "GEMINI_API_KEY environment variable is not set"
                st.rerun()
            else:
                st.session_state["local_llm_stdout"] = "Tailoring...\n"
                prompt_template = st.session_state["master_texts"]["prompt"]
                master_cv = st.session_state["master_texts"]["body"]
                hydrated = prompt_template.format(master_cv=master_cv, job_description=jd_local)

                spinner_msg = (
                    f"Running Gemini ({selected_model})..." if use_cloud else f"Running Ollama ({selected_model})..."
                )
                with st.spinner(spinner_msg):
                    try:
                        f_out = io.StringIO()
                        handler_id = logger.add(f_out, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

                        try:
                            with contextlib.redirect_stdout(f_out), contextlib.redirect_stderr(f_out):
                                if use_cloud:
                                    opts = {
                                        "max_tokens": max_tokens,
                                        "temperature": temperature,
                                        "seed": seed,
                                        "timeout": timeout,
                                    }

                                    result = run_gemini_model(
                                        model=selected_model, prompt_content=hydrated, options=opts
                                    )

                                else:
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

                                    result = run_ollama_model(
                                        model=selected_model, prompt_content=hydrated, options=opts
                                    )
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
                        notes_idx = -1
                        for i in range(start_idx, len(lines)):
                            if "TAILORING JUSTIFICATION REPORT" in lines[i]:
                                end_idx = i
                                notes_idx = i
                                break
                        trimmed_text = "\n".join(lines[start_idx:end_idx]).strip()
                        notes_text = ""
                        if notes_idx != -1:
                            notes_text = "\n".join(lines[notes_idx:]).strip()

                        st.session_state["tailored_body"] = trimmed_text
                        st.session_state["tailored_notes"] = notes_text
                        st.session_state["edited_notes_local"] = notes_text
                        header = st.session_state["master_texts"]["header"]
                        footer = st.session_state["master_texts"]["footer"]
                        full_cv_md = f"{header}\n\n{trimmed_text}\n\n{footer}"
                        if fix_markdown:
                            full_cv_md = process_cv.fix_markdown(full_cv_md)
                        st.session_state["edited_cv_local"] = full_cv_md
                        st.session_state["_persistent_edited_cv_local"] = full_cv_md
                        st.session_state.pop("pdf_bytes", None)
                        st.session_state.pop("local_cv_errors", None)
                        st.session_state.pop("local_cv_checked", None)
                        st.session_state["local_tailor_note"] = "CV Composed successfully!"
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.session_state["local_tailor_error"] = f"LLM Generation Failed: {e}"
                        st.rerun()

        # Message placeholders directly after buttons
        if st.session_state.get("local_tailor_error"):
            st.error(st.session_state["local_tailor_error"])
        if st.session_state.get("local_tailor_warning"):
            st.warning(st.session_state["local_tailor_warning"])
        if st.session_state.get("local_tailor_note"):
            st.info(st.session_state["local_tailor_note"])

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
                    jd_local_val = st.session_state.get("jd_local", "")
                    run_dir, dt_str = get_temp_generation_dir(jd_local_val)
                    f_md_name = str(run_dir / f"cv_{dt_str}.md")
                    pdf_name = str(run_dir / f"cv_{dt_str}.pdf")

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

    # Render Notes expander for tabs[0]
    notes_text_local = st.session_state.get("tailored_notes", "")
    if "edited_notes_local" not in st.session_state:
        st.session_state["edited_notes_local"] = notes_text_local

    st.markdown("---")
    with st.expander("Notes", expanded=True):
        notes_edit_tab_local, notes_preview_tab_local = st.tabs(["Edit", "Preview"])
        with notes_edit_tab_local:
            st.text_area(
                "Notes Edit Local",
                height=300,
                key="edited_notes_local",
                label_visibility="collapsed",
            )
        with notes_preview_tab_local:
            st.markdown(st.session_state.get("edited_notes_local", ""))

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
        st.session_state["edited_cv_manual"] = st.session_state.get("_persistent_edited_cv_manual", full_cv_md)

    edited_full_cv = st.session_state.get("edited_cv_manual", full_cv_md)
    if "edited_cv_manual" in st.session_state:
        st.session_state["_persistent_edited_cv_manual"] = st.session_state["edited_cv_manual"]

    # Dynamic column structure for Step 4 (Markdown) and Step 5 (PDF)
    show_pdf_manual = st.session_state.get("show_pdf_manual_val", True)

    if show_pdf_manual:
        col_md_man, col_pdf_man = st.columns([1, 1])
    else:
        col_md_man = st.container()

    with col_md_man:
        st.subheader("Step 4: Compose CV to Markdown")
        st.toggle(
            "Show PDF Preview", value=st.session_state.get("show_pdf_manual_val", True), key="show_pdf_manual_val"
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            btn_use_manual = st.button(
                "Compose CV manually", key="btn_use_manual_body", type="primary", use_container_width=True
            )
        with col_btn2:
            btn_check_manual_clicked = st.button(
                "Check CV", use_container_width=True, key="btn_check_manual", type="secondary"
            )
        with col_btn3:
            st.download_button(
                "Save Composed CV as Markdown",
                edited_full_cv,
                file_name="cv.md",
                key="dl_md_manual",
                use_container_width=True,
            )

        if btn_check_manual_clicked:
            st.session_state.pop("manual_tailor_error", None)
            st.session_state.pop("manual_tailor_warning", None)
            st.session_state.pop("manual_tailor_note", None)
            if not edited_full_cv.strip():
                st.session_state["manual_tailor_warning"] = "No CV text to check."
                st.rerun()
            else:
                errors = process_cv.check_markdown(edited_full_cv)
                st.session_state["manual_cv_checked"] = True
                if errors:
                    st.session_state["manual_tailor_error"] = (
                        f"CV check failed with {len(errors)} errors:\n"
                        + "\n".join(f"- Line {err.line_num}: {err.msg} (content: `{err.line}`)" for err in errors)
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
                # Extract tailored_notes from manual_body if present
                lines = manual_body.splitlines()
                start_idx = 0
                for i, line in enumerate(lines):
                    if "Summary" in line:
                        start_idx = i
                        break
                end_idx = len(lines)
                notes_idx = -1
                for i in range(start_idx, len(lines)):
                    if "TAILORING JUSTIFICATION REPORT" in lines[i]:
                        end_idx = i
                        notes_idx = i
                        break
                trimmed_text = "\n".join(lines[start_idx:end_idx]).strip()
                notes_text = ""
                if notes_idx != -1:
                    notes_text = "\n".join(lines[notes_idx:]).strip()

                st.session_state["tailored_body"] = trimmed_text
                st.session_state["tailored_notes"] = notes_text
                st.session_state["edited_notes_manual"] = notes_text

                header = st.session_state["master_texts"]["header"]
                footer = st.session_state["master_texts"]["footer"]
                full_cv_md = f"{header}\n\n{trimmed_text}\n\n{footer}"
                full_cv_md = process_cv.fix_markdown(full_cv_md)
                st.session_state["edited_cv_manual"] = full_cv_md
                st.session_state["_persistent_edited_cv_manual"] = full_cv_md
                st.session_state.pop("pdf_bytes", None)
                st.session_state.pop("manual_cv_errors", None)
                st.session_state.pop("manual_cv_checked", None)
                st.session_state["manual_tailor_note"] = "CV Composed manually successfully!"
                st.rerun()

        # Message placeholders directly after buttons
        if st.session_state.get("manual_tailor_error"):
            st.error(st.session_state["manual_tailor_error"])
        if st.session_state.get("manual_tailor_warning"):
            st.warning(st.session_state["manual_tailor_warning"])
        if st.session_state.get("manual_tailor_note"):
            st.info(st.session_state["manual_tailor_note"])

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
                        "Save Composed CV as PDF",
                        st.session_state["pdf_bytes"],
                        file_name="cv.pdf",
                        key="dl_pdf_manual",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "Save Composed CV as PDF", disabled=True, use_container_width=True, key="dl_pdf_manual_disabled"
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
                    jd_manual_val = st.session_state.get("jd_manual", "")
                    run_dir, dt_str = get_temp_generation_dir(jd_manual_val)
                    f_md_name = str(run_dir / f"cv_{dt_str}.md")
                    pdf_name = str(run_dir / f"cv_{dt_str}.pdf")

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

    # Render Notes expander for tabs[1]
    notes_text_man = st.session_state.get("tailored_notes", "")
    if "edited_notes_manual" not in st.session_state:
        st.session_state["edited_notes_manual"] = notes_text_man

    st.markdown("---")
    with st.expander("Notes", expanded=True):
        notes_edit_tab_man, notes_preview_tab_man = st.tabs(["Edit", "Preview"])
        with notes_edit_tab_man:
            st.text_area(
                "Notes Edit Manual",
                height=300,
                key="edited_notes_manual",
                label_visibility="collapsed",
            )
        with notes_preview_tab_man:
            st.markdown(st.session_state.get("edited_notes_manual", ""))

with tabs[2]:
    if "_arbitrary_md_pending" in st.session_state:
        st.session_state["arbitrary_md"] = st.session_state.pop("_arbitrary_md_pending")
    col_md, col_pdf = st.columns([1, 1])
    with col_md:
        st.subheader("Markdown Input")
        col_up, col_chk, col_fix, col_sv = st.columns([5, 2, 2, 2])
        with col_up:
            uploaded_file = st.file_uploader("Upload a Markdown file (.md)", type=["md"], key="uploaded_md_file")
            if uploaded_file is not None:
                file_key = f"last_uploaded_file_{uploaded_file.name}_{uploaded_file.size}"
                if st.session_state.get("last_uploaded_file_key") != file_key:
                    uploaded_content = uploaded_file.getvalue().decode("utf-8")
                    st.session_state["arbitrary_md"] = uploaded_content
                    st.session_state["original_md_content"] = uploaded_content
                    st.session_state["last_uploaded_file_key"] = file_key
                    st.session_state.pop("arbitrary_check_error", None)
                    st.session_state.pop("arbitrary_check_note", None)

        current_md = st.session_state.get("arbitrary_md", "")

        with col_chk:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_check_clicked = st.button(
                "Check",
                key="btn_check_arbitrary_md",
                use_container_width=True,
            )
            if btn_check_clicked:
                st.session_state.pop("arbitrary_check_error", None)
                st.session_state.pop("arbitrary_check_note", None)
                if not current_md.strip():
                    st.session_state["arbitrary_check_error"] = "No markdown content to check."
                else:
                    errors = process_cv.check_markdown(current_md)
                    if errors:
                        st.session_state["arbitrary_check_error"] = (
                            f"CV check failed with {len(errors)} errors:\n"
                            + "\n".join(f"- Line {err.line_num}: {err.msg} (content: `{err.line}`)" for err in errors)
                        )
                    else:
                        st.session_state["arbitrary_check_note"] = "No errors found!"
                st.rerun()

        with col_fix:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_fix_clicked = st.button(
                "Fix",
                key="btn_fix_arbitrary_md",
                use_container_width=True,
            )
            if btn_fix_clicked:
                st.session_state.pop("arbitrary_check_error", None)
                st.session_state.pop("arbitrary_check_note", None)
                if not current_md.strip():
                    st.session_state["arbitrary_check_error"] = "No markdown content to fix."
                else:
                    fixed_md = process_cv.fix_markdown(current_md)
                    st.session_state["_arbitrary_md_pending"] = fixed_md
                    st.session_state["arbitrary_check_note"] = "Markdown formatting fixed!"
                st.rerun()

        with col_sv:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

            def on_save_click() -> None:
                """Save current markdown content to session state."""
                st.session_state["original_md_content"] = st.session_state.get("arbitrary_md", "")

            st.download_button(
                label="Save",
                data=current_md,
                file_name=uploaded_file.name if uploaded_file else "document.md",
                mime="text/markdown",
                key="btn_save_arbitrary_md",
                on_click=on_save_click,
                use_container_width=True,
            )

        if st.session_state.get("arbitrary_check_error"):
            st.error(st.session_state["arbitrary_check_error"])
        if st.session_state.get("arbitrary_check_note"):
            st.info(st.session_state["arbitrary_check_note"])

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
        btn_gen_arb_clicked = st.button("Generate PDF", key="btn_gen_arbitrary_pdf", use_container_width=True)
        if btn_gen_arb_clicked:
            with st.spinner("Generating PDF..."):
                jd_context = st.session_state.get("shared_jd", "")
                run_dir, dt_str = get_temp_generation_dir(jd_context)
                f_md_name = str(run_dir / f"document_{dt_str}.md")
                pdf_name = str(run_dir / f"document_{dt_str}.pdf")

                try:
                    with Path(f_md_name).open("w", encoding="utf-8") as f_md:
                        f_md.write(arbitrary_md)

                    # Fix CV markdown using process_cv
                    fixed_content = process_cv.fix_markdown(arbitrary_md)
                    st.session_state["_arbitrary_md_pending"] = fixed_content

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
    settings_tabs = st.tabs(["CV", "Prompt", "Configuration"])

    with settings_tabs[0]:
        st.subheader("Header")
        header_edit_tab, header_preview_tab = st.tabs(["Edit", "Preview"])
        with header_edit_tab:
            st.session_state["master_texts"]["header"] = st.text_area(
                "Header text",
                value=st.session_state["master_texts"]["header"],
                height=200,
                label_visibility="collapsed",
                key="master_header_editor",
                on_change=_save_master_section,
                args=("master_header_editor", "header"),
            )
        with header_preview_tab:
            st.markdown(st.session_state["master_texts"]["header"])

        st.subheader("Body")
        body_edit_tab, body_preview_tab = st.tabs(["Edit", "Preview"])
        with body_edit_tab:
            st.session_state["master_texts"]["body"] = st.text_area(
                "Body text",
                value=st.session_state["master_texts"]["body"],
                height=400,
                label_visibility="collapsed",
                key="master_body_editor",
                on_change=_save_master_section,
                args=("master_body_editor", "body"),
            )
        with body_preview_tab:
            st.markdown(st.session_state["master_texts"]["body"])

        st.subheader("Footer")
        footer_edit_tab, footer_preview_tab = st.tabs(["Edit", "Preview"])
        with footer_edit_tab:
            st.session_state["master_texts"]["footer"] = st.text_area(
                "Footer text",
                value=st.session_state["master_texts"]["footer"],
                height=200,
                label_visibility="collapsed",
                key="master_footer_editor",
                on_change=_save_master_section,
                args=("master_footer_editor", "footer"),
            )
        with footer_preview_tab:
            st.markdown(st.session_state["master_texts"]["footer"])

    with settings_tabs[1]:
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

    with settings_tabs[2]:
        st.subheader("Config File")

        # Option 1: Choose Config File (opens local file explorer)
        uploaded_config_file = st.file_uploader(
            "Load Config File (Choose from file explorer)",
            type=["yaml", "yml"],
            key="config_file_uploader",
        )
        if uploaded_config_file is not None:
            file_id = f"{uploaded_config_file.name}_{uploaded_config_file.size}"
            if st.session_state.get("_last_loaded_config_file_id") != file_id:
                try:
                    config_data = yaml.safe_load(uploaded_config_file.getvalue())
                    if isinstance(config_data, dict):
                        load_config_data_action(config_data)
                        st.session_state["_last_loaded_config_file_id"] = file_id
                        st.success("Config loaded successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid YAML format.")
                except Exception as e:  # noqa: BLE001
                    st.error(f"Error loading config file: {e}")
        else:
            st.session_state.pop("_last_loaded_config_file_id", None)

        st.markdown("**Or specify path on server:**")

        # Callback to load config automatically when path input is changed
        def on_config_path_change_tab() -> None:
            """Handle changes to config file path."""
            path = st.session_state["config_path_input_val"]
            load_config_action(path)

        config_path_input = st.text_input(
            "Config File Path",
            value=st.session_state.get("config_path_input_val", "../config/config.yaml"),
            key="config_path_input_val",
            on_change=on_config_path_change_tab,
            label_visibility="collapsed",
        )

        if st.button("Load Config Path", key="btn_load_config_tab"):
            load_config_action(config_path_input)
            st.success("Config loaded!")
            st.rerun()

        st.markdown("---")
        st.subheader("API Keys")
        # Gemini API Key configuration
        gemini_api_key_input = st.text_input(
            "Gemini API Key (GEMINI_API_KEY)",
            value=st.session_state.get("gemini_api_key_val", os.environ.get("GEMINI_API_KEY", "")),
            type="password",
            key="gemini_api_key_val",
        )
        if gemini_api_key_input:
            os.environ["GEMINI_API_KEY"] = gemini_api_key_input
