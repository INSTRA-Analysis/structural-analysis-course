"""
styles.py — Shared visual helpers for all lesson pages.

Import at the top of every lesson:
    from styles import apply_styles, lesson_progress, in_practice, key_takeaways
"""

import streamlit as st

# ── Brand colours ────────────────────────────────────────────────────────────
NAVY  = "#1A2B4A"
GOLD  = "#C8972B"
LIGHT = "#F5F7FA"

# ── CSS ──────────────────────────────────────────────────────────────────────
_CSS = """
<style>

/* ── Progress bar — INSTRA navy ─────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1A2B4A 0%, #2E4080 100%);
}

/* ── Metric cards ────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E0E4EC;
    border-radius: 8px;
    padding: 0.9rem 1.1rem 0.75rem;
    box-shadow: 0 1px 4px rgba(26,43,74,0.06);
}
div[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 700;
    color: #1A2B4A;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #5A6070;
}
div[data-testid="stMetricDelta"] svg { display: none; }
div[data-testid="stMetricDelta"] > div {
    font-size: 0.78rem;
    color: #5A6070 !important;
}

/* ── Info box — theory / formula callout (navy) ──────────────── */
div[data-testid="stAlert"] div[role="alert"] {
    border-radius: 6px;
}

/* ── Divider ─────────────────────────────────────────────────── */
hr { border-color: #E0E4EC; }

/* ── Expander header ─────────────────────────────────────────── */
details > summary {
    font-weight: 600;
    color: #1A2B4A;
}

/* ── Code blocks — tighter padding ──────────────────────────── */
.stCodeBlock { border-radius: 6px; }

/* ── Sidebar navigation items ────────────────────────────────── */
section[data-testid="stSidebar"] a {
    font-weight: 500;
}

</style>
"""


def apply_styles():
    """Inject INSTRA brand CSS. Call once per page, right after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def lesson_progress(current: int, total: int = 7, label: str = ""):
    """
    Render a slim progress bar + caption showing where the student is.

    Parameters
    ----------
    current : 1-based lesson number
    total   : total lessons in the sequence (default 7 core + 1 supplementary)
    label   : optional suffix shown in the caption
    """
    st.progress(current / total)
    suffix = f"  ·  {label}" if label else ""
    st.caption(f"Lesson {current} of {total}{suffix}")


def in_practice(text: str):
    """
    Expander with a real-world engineering context note.

    Parameters
    ----------
    text : markdown string shown inside the expander
    """
    with st.expander("🏗️ In engineering practice"):
        st.markdown(text)


def key_takeaways(items: list):
    """
    Styled success box listing key takeaways at the end of a theory section.

    Parameters
    ----------
    items : list of strings (plain text or markdown)
    """
    bullets = "\n".join(f"- {item}" for item in items)
    st.success(f"**Key takeaways from this lesson:**\n\n{bullets}")


def formula_box(label: str, content: str):
    """
    Navy-accented info box for highlighting a key formula or rule.
    content may include markdown but NOT LaTeX (use st.markdown for LaTeX).

    Parameters
    ----------
    label   : short header, e.g. "Equilibrium equations"
    content : markdown body text
    """
    st.info(f"**{label}**\n\n{content}", icon="📐")
