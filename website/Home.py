"""
Home.py — Landing page for the Python for Structural Engineers course.
Run with:  streamlit run Home.py
"""

import streamlit as st

st.set_page_config(
    page_title="Python for Structural Engineers",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/115px-Python-logo-notext.svg.png", width=60)
    st.title("Course Navigation")
    st.markdown("---")
    st.markdown("""
**Lessons:**
1. [Python as Your Calculator](pages/01_L01_Python_Intro.py)
2. [Your Beam on a Number Line](pages/02_L02_Beam_Geometry.py)
3. [Placing Loads on the Beam](pages/03_L03_Loads.py)
4. [Finding Support Reactions](pages/04_L04_Reactions.py)
5. [Shear Force Diagram](pages/05_L05_Shear_Force.py)
6. [Bending Moment Diagram](pages/06_L06_Bending_Moment.py)
7. [Complete Analysis Tool](pages/07_L07_Capstone.py)
""")

# ── Hero section ───────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <h1 style='font-size: 2.8rem; color: #1565C0;'>🏗️ Python for Structural Engineers</h1>
        <h3 style='color: #555; font-weight: 400;'>Simply Supported Beam Analysis — Beginner Course</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ── How this course works ──────────────────────────────────────────────────
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(
        """
        <div style='background:#E3F2FD; border-radius:12px; padding:1.5rem; text-align:center;'>
            <div style='font-size:2.5rem;'>📐</div>
            <h3 style='color:#1565C0;'>Theory</h3>
            <p>Each lesson starts with an interactive diagram you manipulate with sliders.
            Build intuition <em>before</em> writing any code.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown(
        """
        <div style='background:#E8F5E9; border-radius:12px; padding:1.5rem; text-align:center;'>
            <div style='font-size:2.5rem;'>✏️</div>
            <h3 style='color:#2E7D32;'>Practice</h3>
            <p>Write your own Python in an embedded editor. Starter code with blanks
            guides you — fill in the gaps and click <b>Run</b>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_c:
    st.markdown(
        """
        <div style='background:#FFF3E0; border-radius:12px; padding:1.5rem; text-align:center;'>
            <div style='font-size:2.5rem;'>🔍</div>
            <h3 style='color:#E65100;'>Check</h3>
            <p>Compare your code with the worked solution at any time.
            No grades — just learning.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── What you will build ────────────────────────────────────────────────────
st.header("What You Will Build")

st.markdown("""
By the end of this course you will have written a **complete simply supported beam analysis tool** from scratch.
You will be able to:

- Describe any beam geometry (span, cantilevers, support positions) in Python
- Apply point loads and uniformly distributed loads at any position
- Calculate support reactions using equilibrium
- Plot the Shear Force Diagram (SFD) and Bending Moment Diagram (BMD)
- Build interactive diagrams that update live as you change values
- Export a PDF analysis report

The beam we analyse throughout the course:
""")

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "course", "shared"))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    from plot_helpers import draw_beam, draw_loads, draw_reactions
    import beam_solver

    geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
    loads    = [
        {"type": "point", "x": 5.0,  "magnitude": -20.0},
        {"type": "udl",   "x1": 2.0, "x2": 8.0, "w": -5.0},
        {"type": "point", "x": 1.0,  "magnitude": -8.0},
    ]
    R_A, R_B = beam_solver.compute_reactions(geometry, loads)
    x, V     = beam_solver.compute_shear(geometry, loads, R_A, R_B)
    M        = beam_solver.compute_moments(x, V)

    fig = plt.figure(figsize=(14, 8))
    gs  = fig.add_gridspec(3, 1, height_ratios=[1, 1.6, 1.6], hspace=0.1)
    ax_b = fig.add_subplot(gs[0])
    ax_s = fig.add_subplot(gs[1])
    ax_m = fig.add_subplot(gs[2])

    draw_beam(ax_b, geometry)
    draw_loads(ax_b, loads, 10.0)
    draw_reactions(ax_b, 2.0, 8.0, R_A, R_B)

    ax_s.plot(x, V, "#1565C0", lw=2)
    ax_s.fill_between(x, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
    ax_s.fill_between(x, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
    ax_s.axhline(0, color="k", lw=0.8)
    ax_s.set_ylabel("V (kN)", fontsize=9)
    ax_s.grid(True, ls="--", alpha=0.4)
    ax_s.tick_params(labelbottom=False)

    ax_m.plot(x, M, "#1B5E20", lw=2)
    ax_m.fill_between(x, M, 0, where=(M>=0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
    ax_m.fill_between(x, M, 0, where=(M<0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
    ax_m.axhline(0, color="k", lw=0.8)
    ax_m.set_ylabel("M (kN·m)", fontsize=9)
    ax_m.set_xlabel("Position x (m)", fontsize=10)
    ax_m.legend(fontsize=8)
    ax_m.grid(True, ls="--", alpha=0.4)

    for ax_ in [ax_b, ax_s, ax_m]:
        ax_.set_xlim(-0.3, 10.3)

    fig.suptitle(
        f"L = 10 m  |  Pin at 2 m  |  Roller at 8 m  |  "
        f"R_A = {R_A:+.1f} kN  |  R_B = {R_B:+.1f} kN",
        fontsize=10
    )
    st.pyplot(fig, width='stretch')
    plt.close(fig)

except Exception as e:
    st.info(f"(Preview diagram will appear when shared modules are loaded — {e})")

st.markdown("---")

# ── Lesson list ────────────────────────────────────────────────────────────
st.header("Course Lessons")

lessons = [
    ("01", "Python as Your Calculator",
     "Variables, arithmetic, f-strings, `if/else`",
     "Cross-section properties: A, I, Z",
     "pages/01_L01_Python_Intro.py"),
    ("02", "Your Beam on a Number Line",
     "NumPy arrays, matplotlib, loops",
     "Beam geometry, pin vs roller, cantilevers",
     "pages/02_L02_Beam_Geometry.py"),
    ("03", "Placing Loads on the Beam",
     "Dictionaries, functions, conditionals",
     "Sign convention, point loads, UDL",
     "pages/03_L03_Loads.py"),
    ("04", "Finding Support Reactions",
     "Functions with multiple return values, assertions",
     "Equilibrium: ΣFy=0, ΣM=0",
     "pages/04_L04_Reactions.py"),
    ("05", "Shear Force Diagram",
     "Array loops, module imports",
     "SFD — shear as sum of forces to the left",
     "pages/05_L05_Shear_Force.py"),
    ("06", "Bending Moment Diagram",
     "Numerical integration, coloured fills",
     "BMD — moment as integral of shear",
     "pages/06_L06_Bending_Moment.py"),
    ("07", "The Complete Analysis Tool",
     "Putting it all together",
     "Balanced cantilever, optimisation, PDF export",
     "pages/07_L07_Capstone.py"),
]

for num, title, py_topics, struct_topics, page in lessons:
    with st.container():
        c1, c2, c3, c4 = st.columns([0.5, 3, 3, 1.5])
        with c1:
            st.markdown(
                f"<div style='background:#1565C0; color:white; border-radius:50%; "
                f"width:36px; height:36px; display:flex; align-items:center; "
                f"justify-content:center; font-weight:bold;'>{num}</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(f"**{title}**  \n🐍 {py_topics}")
        with c3:
            st.markdown(f"🏗️ {struct_topics}")
        with c4:
            st.page_link(page, label="Open lesson →")
    st.markdown("---")

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:#888; font-size:12px; padding:1rem;'>"
    "Python for Structural Engineers · Simply Supported Beam Course"
    "</div>",
    unsafe_allow_html=True,
)

