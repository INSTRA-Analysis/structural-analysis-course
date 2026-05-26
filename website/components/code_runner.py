"""
code_runner.py — Shared practice section component for all lesson pages.

Provides:
  run_code()       — execute student code, capture output + figures
  practice_block() — render the full practice section in a lesson page
"""

import io
import contextlib
import traceback
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Core execution engine
# ---------------------------------------------------------------------------

def run_code(code: str, pre_defined: dict = None):
    """
    Execute student code safely and return (text_output, figures, error).

    Parameters
    ----------
    code        : str  — the student's code
    pre_defined : dict — variables/functions already available (e.g. np, plt, geometry)

    Returns
    -------
    text_output : str
    figures     : list of matplotlib Figure objects
    error       : str or None
    """
    plt.close("all")

    namespace = {
        "np"          : np,
        "plt"         : plt,
        "__builtins__": __builtins__,
    }
    if pre_defined:
        namespace.update(pre_defined)

    stdout_buf = io.StringIO()
    error_msg  = None

    with contextlib.redirect_stdout(stdout_buf):
        try:
            exec(compile(code, "<student>", "exec"), namespace)
        except Exception:
            error_msg = traceback.format_exc()

    text_output = stdout_buf.getvalue()
    figures     = [plt.figure(n) for n in plt.get_fignums()]

    return text_output, figures, error_msg


# ---------------------------------------------------------------------------
# Practice section renderer
# ---------------------------------------------------------------------------

def practice_block(
    key,
    instructions,
    starter_code,
    solution_code,
    expected_note=None,
    pre_defined=None,
):
    """
    Render a complete practice section: code editor, run button, solution reveal.

    Parameters
    ----------
    key           : str — unique key for this block (used by Streamlit widgets)
    instructions  : str — markdown explaining what the student should do
    starter_code  : str — code pre-filled in the editor (with ___ blanks)
    solution_code : str — full worked solution shown on demand
    expected_note : str — optional hint about the expected output
    pre_defined   : dict — variables pre-loaded into the execution namespace
    """
    st.divider()
    st.subheader("✏️ Practice — Write Your Own Code")
    st.markdown(instructions)

    if expected_note:
        st.info(f"**Expected result:** {expected_note}", icon="🎯")

    # Code editor
    student_code = st.text_area(
        "Your code (edit the blanks `___` and press Run):",
        value=starter_code,
        height=220,
        key=f"editor_{key}",
        help="Replace every ___ with the correct value or expression.",
    )

    col_run, col_space = st.columns([1, 5])
    with col_run:
        run_clicked = st.button("▶ Run my code", key=f"run_{key}", type="primary")

    if run_clicked:
        output, figs, error = run_code(student_code, pre_defined)

        if error:
            # Show only the last line (the actual error) to not overwhelm beginners
            last_line = [ln for ln in error.strip().splitlines() if ln.strip()][-1]
            st.error(f"**Error:** {last_line}")
            with st.expander("Full error details"):
                st.code(error, language="python")
        else:
            st.success("Code ran successfully!", icon="✓")
            if output:
                st.markdown("**Output:**")
                st.code(output, language=None)
            for fig in figs:
                st.pyplot(fig, width='stretch')
                plt.close(fig)
            if not output and not figs:
                st.warning("The code ran but produced no output. "
                           "Did you forget a `print()` statement?")

    # Solution reveal
    with st.expander("💡 Show solution"):
        st.markdown("**Complete solution:**")
        st.code(solution_code, language="python")
        st.markdown("**What it produces:**")
        sol_out, sol_figs, sol_err = run_code(solution_code, pre_defined)
        if sol_err:
            st.error(sol_err)
        if sol_out:
            st.code(sol_out, language=None)
        for fig in sol_figs:
            st.pyplot(fig, width='stretch')
            plt.close(fig)


# ---------------------------------------------------------------------------
# Navigation helper (Previous / Next buttons)
# ---------------------------------------------------------------------------

def lesson_nav(prev_label=None, prev_page=None, next_label=None, next_page=None):
    """Render Previous / Next navigation at the bottom of a lesson page."""
    st.divider()
    cols = st.columns(3)
    if prev_label and prev_page:
        with cols[0]:
            st.page_link(prev_page, label=f"← {prev_label}", icon="⬅️")
    with cols[1]:
        st.markdown(
            "<div style='text-align:center; color:#888; font-size:13px;'>"
            "Python for Structural Engineers</div>",
            unsafe_allow_html=True,
        )
    if next_label and next_page:
        with cols[2]:
            st.page_link(next_page, label=f"{next_label} →", icon="➡️")

