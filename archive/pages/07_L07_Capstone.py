"""Lesson 7 — The Complete Analysis Tool (Capstone)"""

import streamlit as st
import sys, os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "components"))
sys.path.insert(0, os.path.join(BASE, "..", "course", "shared"))

from code_runner import lesson_nav
from plot_helpers import draw_beam, draw_loads, draw_reactions
from styles import apply_styles, lesson_progress, in_practice, key_takeaways
import beam_solver
import sys, os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "..", "course", "shared"))
from notebook_generator import generate_notebook

st.set_page_config(page_title="L07 — Complete Analysis Tool", page_icon="🏆", layout="wide")
apply_styles()

st.title("Lesson 7 — The Complete Analysis Tool")
lesson_progress(7, 7, "Prerequisites: L01–L06  ·  ~90 minutes")
st.markdown("""
You've built every piece of the analysis. Now they all work together in one professional tool.
Use the tabs below — geometry, loads, results, and the balanced cantilever optimiser.
""")

# ══════════════════════════════════════════════════════════════════════════════
# Session state initialisation
# ══════════════════════════════════════════════════════════════════════════════
if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

# Seed capstone from shared session state on first visit to L07
if "cap_loads" not in st.session_state:
    st.session_state.cap_loads = list(st.session_state.loads)
if "cap_last_res" not in st.session_state:
    st.session_state.cap_last_res = None

# ══════════════════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 1. Geometry", "📦 2. Loads", "📊 3. Results", "⚖️ 4. Optimise", "📓 5. Download Notebook"])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Beam Geometry")
    c1, c2 = st.columns([1, 2])
    with c1:
        _g  = st.session_state.geometry
        L   = st.slider("Total length L (m)", 5.0, 20.0, _g["L_total"], 0.5, key="cap_L")
        x_A = st.slider("Pin A position (m)", 0.0, L * 0.45, min(_g["x_A"], L * 0.45), 0.5, key="cap_xA")
        x_B = st.slider("Roller B position (m)", x_A + 0.5, L, max(min(_g["x_B"], L), x_A + 0.5), 0.5, key="cap_xB")
        st.session_state.cap_geo = {"L_total": L, "x_A": x_A, "x_B": x_B}
        cant_L = x_A; cant_R = L - x_B; span = x_B - x_A
        st.markdown(f"""
| Segment | Length |
|---------|--------|
| Left cantilever | **{cant_L:.1f} m** |
| Interior span | **{span:.1f} m** |
| Right cantilever | **{cant_R:.1f} m** |
""")
    with c2:
        geo = st.session_state.cap_geo
        fig, ax = plt.subplots(figsize=(9, 3))
        draw_beam(ax, geo)
        draw_loads(ax, st.session_state.cap_loads, L)
        ax.set_title(f"L={L:.1f} m  |  A={x_A:.1f} m  |  B={x_B:.1f} m", fontsize=10)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Applied Loads")
    c1, c2 = st.columns([1, 1])
    with c1:
        load_type = st.radio("Load type", ["Point load", "UDL"], horizontal=True, key="cap_ltype")
        if load_type == "Point load":
            xp  = st.slider("Position x (m)", 0.0, 10.0, 5.0, 0.5, key="cap_xp")
            mag = st.slider("Magnitude (kN)", -200.0, 200.0, -20.0, 5.0, key="cap_mag")
        else:
            x1 = st.slider("UDL start x1 (m)", 0.0, 9.5, 2.0, 0.5, key="cap_x1")
            x2 = st.slider("UDL end x2 (m)", 0.5, 10.0, 8.0, 0.5, key="cap_x2")
            w  = st.slider("Intensity (kN/m)", -50.0, 50.0, -5.0, 1.0, key="cap_w")

        col_add, col_clr = st.columns(2)
        with col_add:
            if st.button("➕ Add load", type="primary"):
                if load_type == "Point load":
                    st.session_state.cap_loads.append({"type": "point", "x": xp, "magnitude": mag})
                else:
                    if x2 > x1:
                        st.session_state.cap_loads.append({"type": "udl", "x1": x1, "x2": x2, "w": w})
        with col_clr:
            if st.button("🗑️ Clear all"):
                st.session_state.cap_loads = []

    with c2:
        st.markdown("**Current loads:**")
        if not st.session_state.cap_loads:
            st.info("No loads yet. Add some on the left.")
        else:
            total_F = 0.0
            for i, ld in enumerate(st.session_state.cap_loads):
                if ld["type"] == "point":
                    st.markdown(f"**{i+1}.** Point {ld['magnitude']:+.0f} kN at x={ld['x']:.1f} m")
                    total_F += ld["magnitude"]
                else:
                    P_eq = ld["w"] * (ld["x2"] - ld["x1"])
                    st.markdown(f"**{i+1}.** UDL {ld['w']:+.0f} kN/m [{ld['x1']:.1f}–{ld['x2']:.1f} m]  *(equiv. {P_eq:.0f} kN)*")
                    total_F += P_eq
            st.markdown(f"**Total vertical load: {total_F:+.1f} kN**")

# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Analysis Results")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
    with col_btn1:
        run_btn = st.button("▶ Run Analysis", type="primary")
    with col_btn2:
        pdf_btn = st.button("📄 Export PDF")

    if run_btn:
        geo = st.session_state.get("cap_geo", {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0})
        loads = st.session_state.cap_loads
        if not loads:
            st.warning("Go to Tab 2 and add at least one load before running the analysis.")
        else:
            try:
                res = beam_solver.analyse(geo, loads)
                st.session_state.cap_last_res = {"res": res, "geo": geo, "loads": loads}

                R_A, R_B = res["R_A"], res["R_B"]
                x, V, M  = res["x"], res["V"], res["M"]

                # Summary table
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
**Reactions**
| | Value |
|---|---|
| R_A | **{R_A:+.2f} kN** |
| R_B | **{R_B:+.2f} kN** |
""")
                with c2:
                    st.markdown(f"""
**Peak values**
| | Value | Location |
|---|---|---|
| V_max | **{V.max():+.2f} kN** | x = {x[V.argmax()]:.2f} m |
| V_min | **{V.min():+.2f} kN** | x = {x[V.argmin()]:.2f} m |
| M_max | **{M.max():+.2f} kN·m** | x = {x[M.argmax()]:.2f} m |
| M_min | **{M.min():+.2f} kN·m** | x = {x[M.argmin()]:.2f} m |
""")

                # Three-panel figure
                fig = plt.figure(figsize=(12, 9))
                gs  = fig.add_gridspec(3, 1, height_ratios=[1, 1.8, 1.8], hspace=0.08)
                ax_b = fig.add_subplot(gs[0])
                ax_s = fig.add_subplot(gs[1])
                ax_m = fig.add_subplot(gs[2])

                draw_beam(ax_b, geo)
                draw_loads(ax_b, loads, geo["L_total"])
                draw_reactions(ax_b, geo["x_A"], geo["x_B"], R_A, R_B)

                ax_s.plot(x, V, "#1565C0", lw=2)
                ax_s.fill_between(x, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
                ax_s.fill_between(x, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
                ax_s.axhline(0, color="k", lw=0.8)
                ax_s.set_ylabel("V (kN)", fontsize=9)
                ax_s.grid(True, ls="--", alpha=0.35)
                ax_s.tick_params(labelbottom=False)

                ax_m.plot(x, M, "#1B5E20", lw=2)
                ax_m.fill_between(x, M, 0, where=(M>=0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
                ax_m.fill_between(x, M, 0, where=(M<0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
                ax_m.axhline(0, color="k", lw=0.8)
                ax_m.set_ylabel("M (kN·m)", fontsize=9)
                ax_m.set_xlabel("Position x (m)", fontsize=10)
                ax_m.legend(fontsize=8)
                ax_m.grid(True, ls="--", alpha=0.35)

                zc = np.where(np.diff(np.sign(V)))[0]
                for idx in zc:
                    ax_s.axvline(x[idx], color="red", ls=":", lw=1, alpha=0.6)
                    ax_m.axvline(x[idx], color="red", ls=":", lw=1, alpha=0.6)

                xlim = (x[0] - 0.3, x[-1] + 0.3)
                for ax_ in [ax_b, ax_s, ax_m]:
                    ax_.set_xlim(*xlim)
                ax_b.tick_params(labelbottom=False)

                fig.suptitle(
                    f"L={geo['L_total']} m  A={geo['x_A']} m  B={geo['x_B']} m  "
                    f"|  R_A={R_A:+.1f} kN  R_B={R_B:+.1f} kN",
                    fontsize=9, y=1.01
                )
                st.pyplot(fig, width='stretch')
                plt.close(fig)

            except Exception as e:
                st.error(f"Analysis error: {e}")

    if pdf_btn:
        stored = st.session_state.get("cap_last_res")
        if not stored:
            st.warning("Run the analysis first, then export.")
        else:
            res  = stored["res"]
            geo  = stored["geo"]
            loads = stored["loads"]
            R_A, R_B = res["R_A"], res["R_B"]
            x, V, M  = res["x"], res["V"], res["M"]

            fig = plt.figure(figsize=(14, 10))
            gs  = fig.add_gridspec(3, 1, height_ratios=[1, 1.8, 1.8], hspace=0.08)
            ax_b = fig.add_subplot(gs[0])
            ax_s = fig.add_subplot(gs[1])
            ax_m = fig.add_subplot(gs[2])
            draw_beam(ax_b, geo); draw_loads(ax_b, loads, geo["L_total"])
            draw_reactions(ax_b, geo["x_A"], geo["x_B"], R_A, R_B)
            ax_s.plot(x, V, "#1565C0", lw=2)
            ax_s.fill_between(x, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
            ax_s.fill_between(x, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
            ax_s.axhline(0, color="k", lw=0.8); ax_s.set_ylabel("V (kN)", fontsize=9)
            ax_s.grid(True, ls="--", alpha=0.35); ax_s.tick_params(labelbottom=False)
            ax_m.plot(x, M, "#1B5E20", lw=2)
            ax_m.fill_between(x, M, 0, where=(M>=0), color="#A5D6A7", alpha=0.5)
            ax_m.fill_between(x, M, 0, where=(M<0),  color="#FFCDD2", alpha=0.5)
            ax_m.axhline(0, color="k", lw=0.8); ax_m.set_ylabel("M (kN·m)", fontsize=9)
            ax_m.set_xlabel("x (m)", fontsize=10); ax_m.grid(True, ls="--", alpha=0.35)
            fig.suptitle(
                f"Beam Analysis Report  |  L={geo['L_total']} m  A={geo['x_A']} m  B={geo['x_B']} m\n"
                f"R_A={R_A:+.1f} kN  R_B={R_B:+.1f} kN  "
                f"M_max={M.max():+.1f}  M_min={M.min():+.1f} kN·m",
                fontsize=9
            )
            xlim = (x[0]-0.3, x[-1]+0.3)
            for ax_ in [ax_b, ax_s, ax_m]: ax_.set_xlim(*xlim)
            ax_b.tick_params(labelbottom=False)
            plt.tight_layout()
            pdf_path = os.path.join(BASE, "..", "beam_report.pdf")
            fig.savefig(pdf_path, bbox_inches="tight")
            plt.close(fig)
            st.success(f"PDF saved to: `{os.path.abspath(pdf_path)}`")

# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Balanced Cantilever — Optimise Support Position")
    st.markdown("""
For a beam carrying a **full-span UDL**, the peak bending moment is minimised
when the cantilever length is approximately **20.7%** of the total span.
Move the slider to discover this yourself.
""")

    cap_L_opt = st.session_state.get("cap_L", 10.0)
    frac = st.slider(
        "Cantilever fraction (each side)",
        0.01, 0.45, 0.207, 0.005,
        format="%.3f",
        help="Move toward 20.7% to minimise peak moment"
    )

    x_A_opt = frac * cap_L_opt
    x_B_opt = cap_L_opt - x_A_opt
    geo_opt  = {"L_total": cap_L_opt, "x_A": x_A_opt, "x_B": x_B_opt}
    loads_opt = [{"type": "udl", "x1": 0.0, "x2": cap_L_opt, "w": -10.0}]

    col_info, col_plot = st.columns([1, 2])
    with col_info:
        try:
            res_opt = beam_solver.analyse(geo_opt, loads_opt)
            M_sag = res_opt["M"].max()
            M_hog = res_opt["M"].min()
            st.metric("Cantilever", f"{frac*100:.1f}%  ({x_A_opt:.2f} m each side)")
            st.metric("Peak sagging M", f"{M_sag:+.2f} kN·m")
            st.metric("Peak hogging M", f"{M_hog:+.2f} kN·m")
            st.metric("Interior span", f"{x_B_opt - x_A_opt:.2f} m")
            if abs(frac - 0.207) < 0.01:
                st.success("You are near the optimal 20.7%! Sagging and hogging peaks are roughly equal.")
        except Exception as e:
            st.error(str(e))

    with col_plot:
        try:
            fig, (ax_b, ax_m) = plt.subplots(2, 1, figsize=(9, 7),
                                              gridspec_kw={"height_ratios": [1, 2.2]})
            fig.subplots_adjust(hspace=0.07)
            draw_beam(ax_b, geo_opt)
            draw_loads(ax_b, loads_opt, cap_L_opt)
            draw_reactions(ax_b, x_A_opt, x_B_opt, res_opt["R_A"], res_opt["R_B"])
            x_o, M_o = res_opt["x"], res_opt["M"]
            ax_m.plot(x_o, M_o, "#1B5E20", lw=2)
            ax_m.fill_between(x_o, M_o, 0, where=(M_o>=0), color="#A5D6A7", alpha=0.5, label="Sagging")
            ax_m.fill_between(x_o, M_o, 0, where=(M_o<0),  color="#FFCDD2", alpha=0.5, label="Hogging")
            ax_m.axhline(0, color="k", lw=0.8)
            ax_m.set_xlabel("x (m)"); ax_m.set_ylabel("M (kN·m)")
            ax_m.legend(fontsize=8); ax_m.grid(True, ls="--", alpha=0.35)
            xlim = (x_o[0]-0.3, x_o[-1]+0.3)
            ax_b.set_xlim(*xlim); ax_m.set_xlim(*xlim)
            ax_b.tick_params(labelbottom=False)
            fig.suptitle(
                f"Cantilever = {frac*100:.1f}%  |  M_sag={M_sag:+.1f}  M_hog={M_hog:+.1f} kN·m  "
                f"|  Optimal ≈ 20.7%",
                fontsize=9, y=1.01
            )
            st.pyplot(fig, width='stretch')
            plt.close(fig)
        except Exception as e:
            st.error(str(e))

# ── Course complete banner ─────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; background:#E8F5E9; border-radius:12px; padding:2rem;'>
    <h2>🏆 Course Complete!</h2>
    <p style='font-size:1.1rem;'>
    You have built a fully functional simply supported beam analysis tool from scratch.<br>
    <b>Reactions · Shear Force · Bending Moment · Interactive diagrams · PDF export.</b>
    </p>
    <p style='color:#555;'>
    Next: deflection with EI · multi-span continuous beams · section design to code
    </p>
</div>
""", unsafe_allow_html=True)

# ── Tab 5: Download Notebook ─────────────────────────────────────────────────
with tab5:
    st.subheader("Download Your Course Notebook")
    st.markdown("""
The notebook is a self-contained `.ipynb` file you can run in **JupyterLab**,
**VS Code**, or **Google Colab** — no course installation needed.

It contains:
- Your beam geometry and loads pre-filled
- Every solver function defined with annotated comments
- All plots: beam diagram, SFD, BMD, and superposition breakdown
- The complete three-panel analysis figure

**Requirements:** `numpy`, `scipy`, `matplotlib` (standard in any Python environment)
""")

    _geo   = st.session_state.geometry
    _loads = st.session_state.loads

    if not _loads:
        st.info("Add loads in **Lesson 3** first — the notebook will embed your actual beam.")
    else:
        st.markdown(f"""
**Beam that will be embedded:**
L = {_geo['L_total']:.1f} m · Pin A at {_geo['x_A']:.1f} m · Roller B at {_geo['x_B']:.1f} m · {len(_loads)} load(s)
""")
        try:
            _nb_json = generate_notebook(_geo, _loads)
            st.download_button(
                label="⬇ Download notebook (.ipynb)",
                data=_nb_json,
                file_name="beam_analysis_course.ipynb",
                mime="application/json",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Notebook generation failed: {e}")

lesson_nav(
    prev_label="L06 — Bending Moment",
    prev_page="pages/06_L06_Bending_Moment.py",
    next_label="S1 — Superposition",
    next_page="pages/08_L08_Superposition.py",
)

