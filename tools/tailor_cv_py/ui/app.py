import base64
import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

# Make the src package importable when run from repo root
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tailor_cv.llm import DEFAULT_MODEL, call_ollama  # noqa: E402
from tailor_cv.llm_gemini import call_gemini  # noqa: E402
from tailor_cv.pdf import convert_to_pdf  # noqa: E402
from tailor_cv.prompt import DEFAULT_FOOTER, DEFAULT_HEADER, _PROMPTS_DIR  # noqa: E402
from tailor_cv.text import to_plain_text  # noqa: E402

# ── Default settings JSON ─────────────────────────────────────────────────────

_DEFAULT_SETTINGS = json.dumps(
    {
        "GEMINI_API_KEY": "",
        "models": ["gemma4:e2b", "llama3.1:8b", "qwen2.5:7b", "deepseek-r1:7b"],
    },
    indent=2,
)

# ── Session-state initialisation ──────────────────────────────────────────────


def _init() -> None:
    defaults: dict = {
        "header_text": DEFAULT_HEADER.read_text(encoding="utf-8"),
        "footer_text": DEFAULT_FOOTER.read_text(encoding="utf-8"),
        "master_cv": "",
        "job_desc": "",
        "cv_system": (_PROMPTS_DIR / "cv_system.txt").read_text(encoding="utf-8"),
        "cv_user": (_PROMPTS_DIR / "cv_user.txt").read_text(encoding="utf-8"),
        "cov_system": (_PROMPTS_DIR / "cover_letter_system.txt").read_text(encoding="utf-8"),
        "cov_user": (_PROMPTS_DIR / "cover_letter_user.txt").read_text(encoding="utf-8"),
        "settings_json": _DEFAULT_SETTINGS,
        "cv_md": "",
        "cov_md": "",
        "cv_pdf": None,
        "cov_pdf": None,
        "gen_cover": False,
        "model_select": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Helpers ───────────────────────────────────────────────────────────────────


def _settings() -> dict:
    try:
        return json.loads(st.session_state.settings_json)
    except json.JSONDecodeError:
        return {}


def _call_llm(system: str, user_message: str, model: str) -> str:
    if model.startswith("gemini"):
        api_key = _settings().get("GEMINI_API_KEY", "")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        return call_gemini(system=system, user_message=user_message, model=model)
    return call_ollama(system=system, user_message=user_message, model=model)


def _make_pdf(md_text: str) -> bytes | None:
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "doc.md"
        pdf = Path(tmp) / "doc.pdf"
        md.write_text(md_text, encoding="utf-8")
        try:
            convert_to_pdf(str(md), str(pdf))
            return pdf.read_bytes()
        except RuntimeError as exc:
            st.warning(f"PDF generation failed: {exc}")
            return None


def _run_tailor() -> None:
    master_cv = st.session_state.master_cv.strip()
    job_desc = to_plain_text(st.session_state.job_desc.strip())

    if not master_cv:
        st.toast("Master CV is empty — fill the Input tab.", icon="⚠️")
        return
    if not job_desc:
        st.toast("Job Description is empty — fill the Input tab.", icon="⚠️")
        return

    settings = _settings()
    models = settings.get("models", [DEFAULT_MODEL])
    model = st.session_state.model_select or (models[0] if models else DEFAULT_MODEL)

    try:
        user_msg = st.session_state.cv_user.format(cv=master_cv, job_description=job_desc)
    except KeyError as e:
        st.error(f"CV user template placeholder error: {e}")
        return

    with st.spinner(f"Tailoring CV with **{model}** …"):
        tailored = _call_llm(
            system=st.session_state.cv_system,
            user_message=user_msg,
            model=model,
        )

    header = st.session_state.header_text.rstrip()
    footer = st.session_state.footer_text.strip()
    full_cv = f"{header}\n\n{tailored.strip()}\n\n{footer}\n"

    st.session_state.cv_md = full_cv
    with st.spinner("Generating PDF …"):
        st.session_state.cv_pdf = _make_pdf(full_cv)

    if st.session_state.gen_cover:
        try:
            cov_msg = st.session_state.cov_user.format(
                cv=master_cv, job_description=job_desc
            )
        except KeyError as e:
            st.error(f"Cover letter template placeholder error: {e}")
            return

        with st.spinner(f"Generating cover letter with **{model}** …"):
            cover = _call_llm(
                system=st.session_state.cov_system,
                user_message=cov_msg,
                model=model,
            )
        st.session_state.cov_md = cover
        with st.spinner("Generating cover letter PDF …"):
            st.session_state.cov_pdf = _make_pdf(cover)


# ── Reusable widgets ──────────────────────────────────────────────────────────


def _editable_field(label: str, key: str, height: int = 300) -> None:
    """Labelled text area with an optional file-load button."""
    lbl_col, up_col = st.columns([5, 2])
    with lbl_col:
        st.markdown(f"**{label}**")
    with up_col:
        uploaded = st.file_uploader(
            label,
            type=["txt", "md"],
            key=f"_up_{key}",
            label_visibility="collapsed",
        )
        if uploaded:
            st.session_state[key] = uploaded.read().decode("utf-8")
    st.text_area(label, key=key, height=height, label_visibility="collapsed")


def _pdf_panel(pdf: bytes | None, filename: str) -> None:
    if pdf:
        b64 = base64.b64encode(pdf).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="760" style="border:none;border-radius:6px"></iframe>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Download PDF",
            data=pdf,
            file_name=f"{filename}.pdf",
            mime="application/pdf",
        )
    else:
        st.info("PDF will appear here after tailoring.")


# ── Page ──────────────────────────────────────────────────────────────────────


def main() -> None:
    st.set_page_config(page_title="TailorCV", layout="wide", page_icon="📄")
    _init()

    st.title("📄 TailorCV")

    tab_main, tab_input, tab_prompts, tab_settings = st.tabs(
        ["Main", "Input", "Prompts", "Settings"]
    )

    # ── Settings ─────────────────────────────────────────────────────────────
    with tab_settings:
        st.subheader("Settings")
        st.caption(
            "JSON config — `models` list populates the model selector on the Main tab. "
            "Set `GEMINI_API_KEY` to enable Gemini models."
        )
        st.text_area("cfg", key="settings_json", height=360, label_visibility="collapsed")
        if st.button("Validate JSON"):
            try:
                d = json.loads(st.session_state.settings_json)
                st.success(f"Valid — keys: {list(d.keys())}")
            except json.JSONDecodeError as e:
                st.error(str(e))

    # ── Input ─────────────────────────────────────────────────────────────────
    with tab_input:
        c_meta, c_cv, c_jd = st.columns([1, 1, 1])
        with c_meta:
            _editable_field("Header", "header_text", height=220)
            st.divider()
            _editable_field("Footer", "footer_text", height=220)
        with c_cv:
            _editable_field("Master CV", "master_cv", height=680)
        with c_jd:
            _editable_field("Job Description", "job_desc", height=680)

    # ── Prompts ───────────────────────────────────────────────────────────────
    with tab_prompts:
        c_l, c_r = st.columns(2)
        with c_l:
            _editable_field("CV System Prompt", "cv_system", height=340)
            st.divider()
            _editable_field("CV User Template", "cv_user", height=340)
        with c_r:
            _editable_field("Cover Letter System Prompt", "cov_system", height=340)
            st.divider()
            _editable_field("Cover Letter User Template", "cov_user", height=340)

    # ── Main ──────────────────────────────────────────────────────────────────
    with tab_main:
        settings = _settings()
        models = settings.get("models", [DEFAULT_MODEL])
        if st.session_state.model_select not in models:
            st.session_state.model_select = models[0] if models else DEFAULT_MODEL

        ctrl_model, ctrl_cov, ctrl_btn = st.columns([3, 2, 2])
        with ctrl_model:
            st.selectbox("Model", options=models, key="model_select")
        with ctrl_cov:
            st.write("")
            st.checkbox("Generate cover letter", key="gen_cover")
        with ctrl_btn:
            st.write("")
            if st.button("▶  Tailor CV", type="primary", use_container_width=True):
                _run_tailor()

        st.divider()

        show_cover = st.session_state.gen_cover and st.session_state.cov_md
        if show_cover:
            res_cv, res_cov = st.tabs(["Tailored CV", "Cover Letter"])
        else:
            res_cv = st.container()
            res_cov = None

        with res_cv:
            md_col, pdf_col = st.columns(2)
            with md_col:
                st.subheader("Markdown")
                if st.session_state.cv_md:
                    st.markdown(st.session_state.cv_md)
                    st.download_button(
                        "⬇ Download Markdown",
                        data=st.session_state.cv_md,
                        file_name="tailored_cv.md",
                        mime="text/markdown",
                    )
                else:
                    st.info("Tailored CV will appear here after clicking **Tailor CV**.")
            with pdf_col:
                st.subheader("PDF")
                _pdf_panel(st.session_state.cv_pdf, "tailored_cv")

        if res_cov is not None:
            with res_cov:
                md_col, pdf_col = st.columns(2)
                with md_col:
                    st.subheader("Markdown")
                    st.markdown(st.session_state.cov_md)
                    st.download_button(
                        "⬇ Download Markdown",
                        data=st.session_state.cov_md,
                        file_name="cover_letter.md",
                        mime="text/markdown",
                    )
                with pdf_col:
                    st.subheader("PDF")
                    _pdf_panel(st.session_state.cov_pdf, "cover_letter")


if __name__ == "__main__":
    main()
