/* ═══════════════════════════════════════════════════════════════════════════
   BeamAnalysisTool — InstraHub course tool
   ---------------------------------------------------------------------------
   A self-contained, client-side simply-supported / overhanging beam analyser.
   All numerics run in the browser via Pyodide, reusing the SAME vetted Python
   the rest of INSTRA Academy uses:
       beam_solver.py        — reactions, shear, moment, deflection
       notebook_generator.py — the downloadable .ipynb

   Authored as JSX; precompiled to plain JS (beam_tool.js) at build time with
   the CLASSIC React runtime (React.createElement, no module imports) so it runs
   as an ordinary browser script. Rebuild after editing:
       npx babel beam_tool.jsx --config-file ./babel.config.json -o beam_tool.js
   where babel.config.json = {"presets":[["@babel/preset-react",{"runtime":"classic"}]]}

   SIGN CONVENTION BRIDGE (important):
       The sliders give POSITIVE P (kN) and w (kN/m) meaning a DOWNWARD load.
       beam_solver stores downward loads as NEGATIVE magnitude, so we negate
       on the way in:  point → magnitude = -P,  UDL → w = -w.
       Reactions come back positive-upward.
   ═══════════════════════════════════════════════════════════════════════════ */

const { useState, useEffect } = React;

/* ── Design tokens — the single source of colour for the whole tool ──────── */
const C = {
  navyDeep:    "#0f1923",   // page background
  navy:        "#1a2332",   // card / panel background
  navyLight:   "#243044",   // input / stat card background
  navyBorder:  "#2e3d52",   // all borders
  teal:        "#1abc9c",   // primary accent, supports, idle state
  amber:       "#f39c12",   // run button, deflection, UDL
  red:         "#C0392B",   // point loads, errors, tension
  blue:        "#2471A3",   // shear force, compression
  textPrimary: "#e8edf3",
  textMuted:   "#7f8fa4",
  textCode:    "#c9d8ed",
};

const PY_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.6/full/";

/* ═══════════════════════════════════════════════════════════════════════════
   Pyodide singleton — load once, reuse across every tab.
   ═══════════════════════════════════════════════════════════════════════════ */
async function getPyodide() {
  if (window._ihPyodide) return window._ihPyodide;

  const py = await window.loadPyodide({ indexURL: PY_INDEX_URL });
  // numpy + matplotlib only — beam_solver no longer needs scipy (its
  // cumulative_trapezoid is now numpy-only), which avoids the ~30 MB scipy
  // WebAssembly download and dramatically speeds up first load.
  await py.loadPackage(["numpy", "matplotlib"]);

  // Fetch the canonical Python modules and drop them into Pyodide's virtual FS.
  const base = window.IH_PYSRC_BASE;
  for (const name of ["beam_solver.py", "notebook_generator.py"]) {
    const resp = await fetch(`${base}/${name}`);
    if (!resp.ok) throw new Error(`Failed to load ${name} (${resp.status})`);
    py.FS.writeFile(name, await resp.text());
  }

  // Make cwd importable, silence Python stdio, warm up matplotlib (Agg).
  py.runPython(`
import sys, io
sys.path.insert(0, ".")
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
import matplotlib
matplotlib.use("Agg")
import beam_solver
import notebook_generator
`);

  window._ihPyodide = py;
  return py;
}

/* Push the current model into the Python global namespace. */
function setModel(py, m) {
  for (const k of ["L", "A", "B", "E", "I", "P", "xP", "w"]) py.globals.set(k, m[k]);
}

/* ── Python payloads (kept static; parameters injected via globals) ──────── */

const PY_ANALYSIS = `
import json, io, base64
import numpy as np
import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": float(L), "x_A": float(A), "x_B": float(B)}
loads = []
if P != 0:
    loads.append({"type": "point", "x": float(xP), "magnitude": -float(P)})
if w != 0:
    loads.append({"type": "udl", "x1": 0.0, "x2": float(L), "w": -float(w)})

res = bs.analyse(geometry, loads, n_points=1000)
x, V, M = res["x"], res["V"], res["M"]
RA, RB = res["R_A"], res["R_B"]

EI = float(E) * float(I) * 1e-2          # E[GPa]*I[cm^4] -> kN*m^2
defl = bs.compute_deflection(x, M, EI, float(A), float(B))

def _amax(a): return float(np.max(np.abs(a)))
stats = {"RA": float(RA), "RB": float(RB),
         "Mmax": _amax(M), "Vmax": _amax(V), "dmax": _amax(defl)}

# ── Dark, three-panel figure (SFD / BMD / deflection) ──────────────────────
NAVY_BG, PANEL, GRID, TICK = "#0f1923", "#1a2332", "#2e3d52", "#7f8fa4"
fig, axes = plt.subplots(3, 1, figsize=(7.6, 8.4), facecolor=NAVY_BG)
panels = [
    (axes[0], V,    "Shear Force V (kN)",      "#2471A3"),
    (axes[1], M,    "Bending Moment M (kN.m)", "#1abc9c"),
    (axes[2], defl, "Deflection d (mm)",       "#f39c12"),
]
for ax, y, label, color in panels:
    ax.set_facecolor(PANEL)
    ax.plot(x, y, color=color, lw=2)
    ax.axhline(0, color=GRID, lw=1)
    for xs_ in (float(A), float(B)):
        ax.axvline(xs_, color="#1abc9c", ls="--", lw=1, alpha=0.6)
    if P != 0:
        ax.axvline(float(xP), color="#C0392B", ls=":", lw=1, alpha=0.75)
    ax.set_ylabel(label, color=TICK, fontsize=9)
    ax.grid(True, color=GRID, alpha=0.4, lw=0.6)
    ax.tick_params(colors=TICK, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)
axes[2].set_xlabel("Position x (m)", color=TICK, fontsize=9)
fig.tight_layout()

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=120, facecolor=NAVY_BG)
plt.close(fig)
img = base64.b64encode(buf.getvalue()).decode("ascii")

json.dumps({"stats": stats, "plot": img})
`;

// Size the SECTION for the model's fixed load case, checking BOTH limit states:
//   • Serviceability (deflection): δmax ∝ 1/(E·I) → required I.
//   • Strength (bending):  σ = Mmax/Z ≤ σ_allow → required Z.
// Deflection scales exactly as 1/(E·I), so we get the constant K = δ·EI once
// (by evaluating at EI = 1) and solve directly — no brute-force sweep.
//
// Units:  M [kN·m], I [cm⁴], E [GPa], Z [cm³], σ [MPa].
//   EI[kN·m²] = E·I·1e-2     (1 GPa·1 cm⁴ = 1e-2 kN·m²)
//   σ[MPa]    = 1000·M/Z     (1 kN·m / 1 cm³ = 1000 MPa)
const PY_SIZE_SECTION = `
import json
import numpy as np
import beam_solver as bs

geometry = {"L_total": float(L), "x_A": float(A), "x_B": float(B)}
loads = []
if P != 0:
    loads.append({"type": "point", "x": float(xP), "magnitude": -float(P)})
if w != 0:
    loads.append({"type": "udl", "x1": 0.0, "x2": float(L), "w": -float(w)})

res  = bs.analyse(geometry, loads, n_points=1000)
Mmax = float(np.max(np.abs(res["M"])))           # kN·m

E_gpa     = float(E)
dlim      = float(delta_lim)
sig_allow = float(sigma_allow)                   # MPa
Z_cur     = float(Zsec)                          # cm³

# ── Serviceability: deflection ─────────────────────────────────────────────
# δmax when EI = 1  ⇒  K (mm·kN·m²). For any EI:  δmax = K / EI.
d_unit   = bs.compute_deflection(res["x"], res["M"], 1.0, float(A), float(B))
K        = float(np.max(np.abs(d_unit)))
EI_cur   = E_gpa * float(I) * 1e-2
dmax_cur = K / EI_cur if EI_cur > 0 else float("inf")
EI_req   = K / dlim if dlim > 0 else float("inf")
I_req    = 100.0 * EI_req / E_gpa if E_gpa > 0 else float("inf")
util_def = dmax_cur / dlim if dlim > 0 else float("inf")

# ── Strength: bending stress ───────────────────────────────────────────────
sigma_max = 1000.0 * Mmax / Z_cur     if Z_cur > 0     else float("inf")
Z_req     = 1000.0 * Mmax / sig_allow if sig_allow > 0 else float("inf")
util_str  = sigma_max / sig_allow     if sig_allow > 0 else float("inf")

governs = "deflection" if util_def >= util_str else "strength"

json.dumps({
    "Mmax":      Mmax,
    "span":      float(B) - float(A),
    # deflection
    "I_req":     I_req,    "I_cur":    float(I),
    "dmax_cur":  dmax_cur, "dlim":     dlim,
    "util_def":  util_def, "pass_def": bool(dmax_cur <= dlim),
    # strength
    "Z_req":     Z_req,     "Z_cur":     Z_cur,
    "sigma_max": sigma_max, "sig_allow": sig_allow,
    "util_str":  util_str,  "pass_str":  bool(sigma_max <= sig_allow),
    # combined
    "governs":   governs,
    "passes":    bool(dmax_cur <= dlim and sigma_max <= sig_allow),
})
`;

const PY_NOTEBOOK = `
import notebook_generator as ng
geometry = {"L_total": float(L), "x_A": float(A), "x_B": float(B)}
loads = []
if P != 0:
    loads.append({"type": "point", "x": float(xP), "magnitude": -float(P)})
if w != 0:
    loads.append({"type": "udl", "x1": 0.0, "x2": float(L), "w": -float(w)})
ng.generate_notebook(geometry, loads)
`;

/* ═══════════════════════════════════════════════════════════════════════════
   Practice ("learn by coding") — runs student Python in the SAME Pyodide
   kernel, capturing stdout, matplotlib figures and errors. Mirrors the
   Streamlit course's practice_block (code_runner.py).
   ═══════════════════════════════════════════════════════════════════════════ */

// Execute the string in the global STUDENT_CODE; returns {out, err, figs[]}.
const PY_RUN_STUDENT = `
import io, sys, json, base64, traceback
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import beam_solver

plt.close("all")
_buf = io.StringIO()
_err = None
_ns = {"np": np, "plt": plt, "beam_solver": beam_solver, "__name__": "__student__"}
_old = sys.stdout
sys.stdout = _buf
try:
    exec(compile(STUDENT_CODE, "<student>", "exec"), _ns)
except Exception:
    _err = traceback.format_exc()
finally:
    sys.stdout = _old

_figs = []
for _n in plt.get_fignums():
    _f = plt.figure(_n)
    _b = io.BytesIO()
    _f.savefig(_b, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    _figs.append(base64.b64encode(_b.getvalue()).decode("ascii"))
plt.close("all")

json.dumps({"out": _buf.getvalue(), "err": _err, "figs": _figs})
`;

/* Exercises ported from the INSTRA lesson pages. Data-driven — add more by
   appending objects here (each: title, instructions, expected, starter, solution). */
const EXERCISES = [
  {
    id: "geometry",
    title: "1 · Beam geometry",
    instructions: "Three numbers describe the beam. Fill each ___ so the printed segment lengths are correct.",
    expected: "Left 2.00 m · Span 6.00 m · Right 2.00 m",
    starter: `# A beam is described by three numbers (metres):
L_total = 10.0     # total length
x_A     = 2.0      # pin support position
x_B     = 8.0      # roller support position

left_cantilever  = ___              # distance from x=0 to the pin
interior_span    = ___ - x_A        # pin to roller
right_cantilever = L_total - ___    # roller to right end

print(f"Left cantilever : {left_cantilever:.2f} m")
print(f"Interior span   : {interior_span:.2f} m")
print(f"Right cantilever: {right_cantilever:.2f} m")
`,
    solution: `L_total = 10.0
x_A     = 2.0
x_B     = 8.0

left_cantilever  = x_A
interior_span    = x_B - x_A
right_cantilever = L_total - x_B

print(f"Left cantilever : {left_cantilever:.2f} m")
print(f"Interior span   : {interior_span:.2f} m")
print(f"Right cantilever: {right_cantilever:.2f} m")
`,
  },
  {
    id: "reactions",
    title: "2 · Support reactions",
    instructions: "The loads are given. Just fill the three blanks in the equilibrium maths: the moment arm about A, and the two equations that give R_B and R_A. Then the self-check confirms ΣFy ≈ 0.",
    expected: "R_A ≈ +31.0 kN · R_B ≈ +35.0 kN · ΣFy ≈ 0",
    starter: `# Reactions for: L = 10 m, pin A at 2 m, roller B at 8 m.
# The loads are already defined — focus on the equilibrium maths below.
geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 3.0,  "magnitude": -30.0},    # -30 kN at x = 3 m
    {"type": "udl",   "x1": 4.0, "x2": 10.0, "w": -6.0}, # -6 kN/m from 4-10 m
]

x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
span = x_B - x_A

total_force = 0.0
total_M_A   = 0.0                       # moment of the loads about A
for ld in loads:
    if ld["type"] == "point":
        total_force += ld["magnitude"]
        total_M_A   += ld["magnitude"] * (ld["x"] - ___)   # moment arm from A
    elif ld["type"] == "udl":
        P_eq = ld["w"] * (ld["x2"] - ld["x1"])             # resultant of the UDL
        x_c  = (ld["x1"] + ld["x2"]) / 2                   # its centroid
        total_force += P_eq
        total_M_A   += P_eq * (x_c - x_A)

# Two equilibrium equations — fill each right-hand side:
R_B = -total_M_A / ___        # ΣM about A = 0   -> divide by the span
R_A = -total_force - ___      # ΣFy = 0          -> subtract R_B

print(f"R_A = {R_A:+.2f} kN")
print(f"R_B = {R_B:+.2f} kN")
print(f"Check ΣFy = {R_A + R_B + total_force:.2e} kN  (≈ 0)")
`,
    solution: `geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 3.0,  "magnitude": -30.0},
    {"type": "udl",   "x1": 4.0, "x2": 10.0, "w": -6.0},
]

x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
span = x_B - x_A

total_force = 0.0
total_M_A   = 0.0
for ld in loads:
    if ld["type"] == "point":
        total_force += ld["magnitude"]
        total_M_A   += ld["magnitude"] * (ld["x"] - x_A)   # moment arm from A
    elif ld["type"] == "udl":
        P_eq = ld["w"] * (ld["x2"] - ld["x1"])
        x_c  = (ld["x1"] + ld["x2"]) / 2
        total_force += P_eq
        total_M_A   += P_eq * (x_c - x_A)

R_B = -total_M_A / span        # ΣM about A = 0
R_A = -total_force - R_B       # ΣFy = 0

print(f"R_A = {R_A:+.2f} kN")
print(f"R_B = {R_B:+.2f} kN")
print(f"Check ΣFy = {R_A + R_B + total_force:.2e} kN  (≈ 0)")
`,
  },
  {
    id: "solver",
    title: "3 · Call the solver",
    instructions: "beam_solver is already imported as bs. Each tab focuses on CALLING a function correctly — fill every ___ : the arguments you pass in, and the result-dict key you read back. analyse(geometry, loads) returns a dict with keys \"R_A\", \"R_B\", \"x\", \"V\", \"M\".",
    expected: "Prints R_A/R_B and shows the selected diagram.",
    variants: [
      {
        label: "Shear (SFD)",
        starter: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

# Call analyse with the two arguments it needs:
res = bs.analyse(___, ___)

print(f"R_A = {res['R_A']:+.2f} kN   R_B = {res['R_B']:+.2f} kN")

V = res["___"]          # which key holds the shear force?

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], V, color="#1565C0", lw=2)
ax.fill_between(res["x"], V, 0, alpha=0.3, color="#90CAF9")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("x (m)"); ax.set_ylabel("V (kN)")
ax.set_title("Shear Force Diagram")
plt.show()
`,
        solution: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

res = bs.analyse(geometry, loads)        # arguments: geometry, then loads
print(f"R_A = {res['R_A']:+.2f} kN   R_B = {res['R_B']:+.2f} kN")

V = res["V"]                              # "V" is the shear force array

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], V, color="#1565C0", lw=2)
ax.fill_between(res["x"], V, 0, alpha=0.3, color="#90CAF9")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("x (m)"); ax.set_ylabel("V (kN)")
ax.set_title("Shear Force Diagram")
plt.show()
# Shear is the sum of vertical forces to the LEFT of each section — it jumps
# at every point load and reaction, and slopes under a UDL.`,
      },
      {
        label: "Moment (BMD)",
        starter: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

res = bs.analyse(geometry, ___)     # pass the loads list as the 2nd argument
print(f"R_A = {res['R_A']:+.2f} kN   R_B = {res['R_B']:+.2f} kN")

M = res["___"]                      # which key holds the bending moment?

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], M, color="#1B5E20", lw=2)
ax.fill_between(res["x"], M, 0, alpha=0.3, color="#A5D6A7")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("x (m)"); ax.set_ylabel("M (kN·m)")
ax.set_title("Bending Moment Diagram")
plt.show()
`,
        solution: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

res = bs.analyse(geometry, loads)
print(f"R_A = {res['R_A']:+.2f} kN   R_B = {res['R_B']:+.2f} kN")

M = res["M"]                              # "M" is the bending moment array

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], M, color="#1B5E20", lw=2)
ax.fill_between(res["x"], M, 0, alpha=0.3, color="#A5D6A7")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("x (m)"); ax.set_ylabel("M (kN·m)")
ax.set_title("Bending Moment Diagram")
plt.show()
# Moment is the integral of shear — it peaks exactly where V crosses zero.`,
      },
      {
        label: "Deflection",
        starter: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

E = 200.0      # GPa
I = 8000.0     # cm^4
EI = E * I * ___          # conversion factor GPa·cm^4 -> kN·m^2  (it is 1e-2)

res = bs.analyse(geometry, loads)

# compute_deflection(x, M, EI, x_A, x_B) — fill the moment array and EI:
defl = bs.compute_deflection(res["x"], res["___"], ___,
                             geometry["x_A"], geometry["x_B"])

print(f"Max deflection = {abs(defl).max():.2f} mm")

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], defl, color="#E65100", lw=2)
ax.axhline(0, color="k", lw=0.8)
for xs in (geometry["x_A"], geometry["x_B"]):
    ax.axvline(xs, color="#1abc9c", ls="--", lw=1)
ax.set_xlabel("x (m)"); ax.set_ylabel("deflection (mm)")
ax.set_title("Deflection")
plt.show()
`,
        solution: `import matplotlib.pyplot as plt
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0, "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

E = 200.0
I = 8000.0
EI = E * I * 1e-2                         # -> kN·m^2

res = bs.analyse(geometry, loads)
defl = bs.compute_deflection(res["x"], res["M"], EI,
                             geometry["x_A"], geometry["x_B"])

print(f"Max deflection = {abs(defl).max():.2f} mm")

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(res["x"], defl, color="#E65100", lw=2)
ax.axhline(0, color="k", lw=0.8)
for xs in (geometry["x_A"], geometry["x_B"]):
    ax.axvline(xs, color="#1abc9c", ls="--", lw=1)
ax.set_xlabel("x (m)"); ax.set_ylabel("deflection (mm)")
ax.set_title("Deflection")
plt.show()
# Arguments go in order: x, M, EI, then the two support positions.
# Stiffer section (bigger E or I) => smaller deflection. Try I = 20000.`,
      },
    ],
  },
  {
    id: "capstone",
    title: "4 · Challenge — build the solver",
    instructions: "Optional challenge — come back once the first three feel comfortable. Reconstruct the core of beam_solver yourself: reactions from equilibrium, shear by the section-cut method, moment by integrating shear. Fill in your beam data and every ___, then the self-check compares your result to the library bs.analyse(). Goal: match it exactly. (Don't worry if it takes a few tries — Show solution is right there.)",
    expected: "Match library: True  (your R_A/R_B/V/M equal beam_solver's).",
    starter: `import numpy as np
import beam_solver as bs        # used only for the final self-check

# ── 1. Your beam — fill in the numbers ─────────────────────────────────────
geometry = {"L_total": ___, "x_A": ___, "x_B": ___}
loads = [
    {"type": "point", "x": ___, "magnitude": ___},      # e.g. -50 kN at x=5
    {"type": "udl",   "x1": ___, "x2": ___, "w": ___},  # e.g. -10 kN/m, 0..L
]

# ── 2. Reactions: two equilibrium equations ────────────────────────────────
def my_reactions(geometry, loads):
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    span = x_B - x_A
    total_force = 0.0          # ΣFy of applied loads
    total_M_A   = 0.0          # Σ moments of applied loads about A
    for ld in loads:
        if ld["type"] == "point":
            total_force += ld["magnitude"]
            total_M_A   += ld["magnitude"] * (ld["x"] - x_A)
        elif ld["type"] == "udl":
            P_eq = ld["w"] * (ld["x2"] - ld["x1"])     # resultant of the UDL
            x_c  = (ld["x1"] + ld["x2"]) / 2           # its centroid
            total_force += P_eq
            total_M_A   += P_eq * (x_c - x_A)
    R_B = -total_M_A / ___        # ΣM about A = 0  -> solve for R_B
    R_A = -total_force - ___      # ΣFy = 0          -> solve for R_A
    return R_A, R_B

# ── 3. Shear: sum of forces to the LEFT of each cut (vectorised) ────────────
def my_shear(geometry, loads, R_A, R_B, x):
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    V = np.zeros_like(x)
    V += R_A * (x >= x_A)         # pin reaction acts from x_A onward
    V += R_B * (x >= ___)         # roller reaction acts from where onward?
    for ld in loads:
        if ld["type"] == "point":
            V += ld["magnitude"] * (x >= ld["x"])
        elif ld["type"] == "udl":
            V += ld["w"] * np.maximum(np.minimum(x, ld["x2"]) - ld["x1"], 0.0)
    return V

# ── 4. Moment: integrate the shear force ───────────────────────────────────
def my_moment(x, V):
    return bs.cumulative_trapezoid(V, x, initial=0.0)

# ── 5. Run your solver ─────────────────────────────────────────────────────
x = np.linspace(0.0, geometry["L_total"], 500)
R_A, R_B = my_reactions(geometry, loads)
V = my_shear(geometry, loads, R_A, R_B, x)
M = my_moment(x, V)
print(f"My solver : R_A = {R_A:+.2f} kN   R_B = {R_B:+.2f} kN")

# ── 6. Self-check against the library ──────────────────────────────────────
ref = bs.analyse(geometry, loads, n_points=500)
print(f"Library   : R_A = {ref['R_A']:+.2f} kN   R_B = {ref['R_B']:+.2f} kN")
match = np.allclose(V, ref["V"], atol=1e-6) and np.allclose(M, ref["M"], atol=1e-6)
print("Match library:", match)
`,
    solution: `import numpy as np
import beam_solver as bs

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 5.0,  "magnitude": -50.0},
    {"type": "udl",   "x1": 0.0, "x2": 10.0, "w": -10.0},
]

def my_reactions(geometry, loads):
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    span = x_B - x_A
    total_force = 0.0
    total_M_A   = 0.0
    for ld in loads:
        if ld["type"] == "point":
            total_force += ld["magnitude"]
            total_M_A   += ld["magnitude"] * (ld["x"] - x_A)
        elif ld["type"] == "udl":
            P_eq = ld["w"] * (ld["x2"] - ld["x1"])
            x_c  = (ld["x1"] + ld["x2"]) / 2
            total_force += P_eq
            total_M_A   += P_eq * (x_c - x_A)
    R_B = -total_M_A / span        # ΣM about A = 0
    R_A = -total_force - R_B       # ΣFy = 0
    return R_A, R_B

def my_shear(geometry, loads, R_A, R_B, x):
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    V = np.zeros_like(x)
    V += R_A * (x >= x_A)
    V += R_B * (x >= x_B)          # roller acts from x_B onward
    for ld in loads:
        if ld["type"] == "point":
            V += ld["magnitude"] * (x >= ld["x"])
        elif ld["type"] == "udl":
            V += ld["w"] * np.maximum(np.minimum(x, ld["x2"]) - ld["x1"], 0.0)
    return V

def my_moment(x, V):
    return bs.cumulative_trapezoid(V, x, initial=0.0)

x = np.linspace(0.0, geometry["L_total"], 500)
R_A, R_B = my_reactions(geometry, loads)
V = my_shear(geometry, loads, R_A, R_B, x)
M = my_moment(x, V)
print(f"My solver : R_A = {R_A:+.2f} kN   R_B = {R_B:+.2f} kN")

ref = bs.analyse(geometry, loads, n_points=500)
print(f"Library   : R_A = {ref['R_A']:+.2f} kN   R_B = {ref['R_B']:+.2f} kN")
match = np.allclose(V, ref["V"], atol=1e-6) and np.allclose(M, ref["M"], atol=1e-6)
print("Match library:", match)
# The three ___ were: R_B denominator = span, R_A = -total_force - R_B,
# and the roller reaction acts from x_B onward.`,
  },
];

/* ── Small formatting helper ─────────────────────────────────────────────── */
const fmt = (v, n = 2) => (Number.isFinite(v) ? v.toFixed(n) : "—");

/* ═══════════════════════════════════════════════════════════════════════════
   SVG beam diagram — pure SVG, no libraries. Spec from BEAM_TOOL_BRIEF.
   ═══════════════════════════════════════════════════════════════════════════ */
function BeamDiagram({ L, A, B, P, xP, w }) {
  const W = 560, H = 140, padL = 40, padR = 40, beamY = 80;
  const beamW = W - padL - padR;          // 480
  const pxPerM = beamW / L;
  const X = (m) => padL + m * pxPerM;

  const xA = X(A), xB = X(B), xPp = X(Math.min(xP, L));

  // UDL arrows (7 evenly spaced) — only drawn when w > 0
  const udlArrows = [];
  if (w > 0) {
    for (let i = 0; i < 7; i++) {
      const ax = padL + (beamW * i) / 6;
      udlArrows.push(
        <line key={`u${i}`} x1={ax} y1={beamY - 28} x2={ax} y2={beamY - 8}
              stroke={C.amber} strokeWidth="1.5" markerEnd="url(#udlhead)" />
      );
    }
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W, display: "block" }}>
      <defs>
        <marker id="plhead" markerWidth="9" markerHeight="9" refX="4.5" refY="8"
                orient="auto"><path d="M0,0 L9,0 L4.5,9 z" fill={C.red} /></marker>
        <marker id="udlhead" markerWidth="8" markerHeight="8" refX="4" refY="7"
                orient="auto"><path d="M0,0 L8,0 L4,8 z" fill={C.amber} /></marker>
      </defs>

      {/* Overhang shading */}
      {A > 0 && <rect x={padL} y={60} width={xA - padL} height={40} fill="#C0392B14" />}
      {B < L && <rect x={xB} y={60} width={padL + beamW - xB} height={40} fill="#C0392B14" />}

      {/* Beam */}
      <rect x={padL} y={beamY - 5} width={beamW} height={10} rx={2}
            fill={C.navyLight} stroke={C.navyBorder} />

      {/* UDL */}
      {w > 0 && (
        <g>
          <line x1={padL} y1={beamY - 28} x2={padL + beamW} y2={beamY - 28}
                stroke={C.amber} strokeWidth="1.5" />
          {udlArrows}
          <text x={padL + beamW / 2} y={beamY - 34} textAnchor="middle"
                fill={C.amber} fontSize="11">{w} kN/m</text>
        </g>
      )}

      {/* Point load */}
      {P > 0 && (
        <g>
          <line x1={xPp} y1={beamY - 35} x2={xPp} y2={beamY - 6}
                stroke={C.red} strokeWidth="2.5" markerEnd="url(#plhead)" />
          <text x={xPp} y={beamY - 40} textAnchor="middle"
                fill={C.red} fontSize="11">{P} kN</text>
        </g>
      )}

      {/* Pin support at A (filled triangle, point up at beam) */}
      <polygon points={`${xA},${beamY + 5} ${xA - 7},${beamY + 21} ${xA + 7},${beamY + 21}`}
               fill={C.teal} />
      <text x={xA} y={beamY + 34} textAnchor="middle" fill={C.textMuted} fontSize="10">
        A ({fmt(A, 1)} m)
      </text>

      {/* Roller support at B (open triangle + circle) */}
      <polygon points={`${xB},${beamY + 5} ${xB - 7},${beamY + 21} ${xB + 7},${beamY + 21}`}
               fill="none" stroke={C.teal} strokeWidth="1.5" />
      <circle cx={xB} cy={beamY + 26} r={5} fill="none" stroke={C.teal} strokeWidth="1.5" />
      <text x={xB} y={beamY + 40} textAnchor="middle" fill={C.textMuted} fontSize="10">
        B ({fmt(B, 1)} m)
      </text>

      {/* Dimension */}
      <text x={padL + beamW / 2} y={H - 6} textAnchor="middle"
            fill={C.textMuted} fontSize="10">L = {fmt(L, 1)} m</text>
    </svg>
  );
}

/* ── Reusable bits ───────────────────────────────────────────────────────── */
function SectionHead({ children }) {
  return (
    <div style={{
      borderLeft: `3px solid ${C.teal}`, paddingLeft: 10, margin: "18px 0 12px",
      fontSize: 13, fontWeight: 700, letterSpacing: "0.04em", color: C.textPrimary,
      textTransform: "uppercase",
    }}>{children}</div>
  );
}

function SliderRow({ label, value, unit, min, max, step, onChange }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
        <span style={{ color: C.textPrimary }}>{label}</span>
        <span style={{ color: C.teal, fontWeight: 700 }}>{fmt(value, 1)} {unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
             onChange={(e) => onChange(parseFloat(e.target.value))}
             style={{ width: "100%", accentColor: C.teal, height: 4, marginTop: 6 }} />
      <div style={{ display: "flex", justifyContent: "space-between",
                    fontSize: 10, color: C.navyBorder }}>
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  );
}

function StatCard({ label, value, unit, color }) {
  return (
    <div style={{
      background: C.navyLight, border: `1px solid ${C.navyBorder}`,
      borderTop: `3px solid ${color}`, borderRadius: 6, padding: "12px 16px",
      minWidth: 120, flex: "1 1 120px",
    }}>
      <div style={{ fontSize: 11, color: C.textMuted }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 11, color: C.textMuted }}>{unit}</div>
    </div>
  );
}

const btnPrimary = {
  background: C.amber, color: C.navyDeep, fontWeight: 700, border: "none",
  borderRadius: 6, padding: "9px 22px", fontSize: 13, cursor: "pointer",
  fontFamily: "inherit",
};
const btnGhost = {
  background: "transparent", color: C.textPrimary, border: `1px solid ${C.navyBorder}`,
  borderRadius: 6, padding: "9px 22px", fontSize: 13, cursor: "pointer",
  fontFamily: "inherit",
};
const disabledBtn = { opacity: 0.45, cursor: "not-allowed" };

/* ═══════════════════════════════════════════════════════════════════════════
   Optimise tab — self-contained, owns its local state.
   ═══════════════════════════════════════════════════════════════════════════ */
function OptimiseTab({ model, pyReady, setTab }) {
  const [limit, setLimit] = useState(20);     // deflection limit, mm
  const [sigAllow, setSigAllow] = useState(165);  // allowable bending stress, MPa
  const [Zsec, setZsec] = useState(600);      // current section modulus, cm³
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);

  async function run() {
    setBusy(true); setErr(null);
    try {
      const py = await getPyodide();
      setModel(py, model);
      py.globals.set("delta_lim", limit);
      py.globals.set("sigma_allow", sigAllow);
      py.globals.set("Zsec", Zsec);
      setRes(JSON.parse(py.runPython(PY_SIZE_SECTION)));
    } catch (e) { setErr(String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <SectionHead>Optimise the section (most economical)</SectionHead>
      <p style={{ color: C.textMuted, fontSize: 13, marginBottom: 12 }}>
        The load case (P = {model.P} kN at {fmt(model.xP, 1)} m, UDL = {model.w} kN/m),
        geometry and material (E = {model.E} GPa) are <em>given</em>. The section must satisfy
        <strong style={{ color: C.textPrimary }}> two limit states</strong> — deflection
        (needs enough <code>I</code>) and bending strength (needs enough section modulus{" "}
        <code>Z</code>). Whichever is more utilised <strong>governs</strong> the size.
      </p>

      <SliderRow label="Deflection limit δ_lim" value={limit} unit="mm"
                 min={2} max={50} step={1} onChange={setLimit} />
      <SliderRow label="Allowable bending stress σ_allow" value={sigAllow} unit="MPa"
                 min={50} max={400} step={5} onChange={setSigAllow} />
      <SliderRow label="Current section modulus Z" value={Zsec} unit="cm³"
                 min={50} max={5000} step={10} onChange={setZsec} />

      <button style={{ ...btnPrimary, ...((!pyReady || busy) ? disabledBtn : {}) }}
              disabled={!pyReady || busy} onClick={run}>
        {busy ? "Sizing…" : "Size the section"}
      </button>

      {err && <p style={{ color: C.red, fontSize: 13, marginTop: 12 }}>{err}</p>}

      {res && (
        <div>
          <div style={{ fontSize: 12, color: C.textMuted, margin: "16px 0 6px" }}>
            SERVICEABILITY — deflection
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <StatCard label="Required I (min)" value={fmt(res.I_req, 0)} unit="cm⁴" color={C.teal} />
            <StatCard label="Current I" value={fmt(res.I_cur, 0)} unit="cm⁴" color={C.blue} />
            <StatCard label="Current δmax" value={fmt(res.dmax_cur, 2)}
                      unit={`mm (limit ${fmt(res.dlim, 0)})`} color={C.amber} />
            <StatCard label="Utilisation" value={fmt(res.util_def * 100, 0)}
                      unit="% of limit" color={res.pass_def ? C.teal : C.red} />
          </div>

          <div style={{ fontSize: 12, color: C.textMuted, margin: "16px 0 6px" }}>
            STRENGTH — bending stress (Mmax = {fmt(res.Mmax, 1)} kN·m)
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <StatCard label="Required Z (min)" value={fmt(res.Z_req, 0)} unit="cm³" color={C.teal} />
            <StatCard label="Current Z" value={fmt(res.Z_cur, 0)} unit="cm³" color={C.blue} />
            <StatCard label="σmax" value={fmt(res.sigma_max, 1)}
                      unit={`MPa (allow ${fmt(res.sig_allow, 0)})`} color={C.amber} />
            <StatCard label="Utilisation" value={fmt(res.util_str * 100, 0)}
                      unit="% of allow" color={res.pass_str ? C.teal : C.red} />
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
            <StatCard label="Governing limit state" value={res.governs === "deflection" ? "Deflection" : "Strength"}
                      unit="" color={C.amber} />
            <StatCard label="Overall verdict" value={res.passes ? "PASS" : "FAIL"} unit=""
                      color={res.passes ? C.teal : C.red} />
          </div>

          <p style={{ color: C.textMuted, fontSize: 13, marginTop: 14 }}>
            The economical section is the smallest one meeting <strong>both</strong> limits:{" "}
            <strong style={{ color: C.teal }}>I ≥ {fmt(res.I_req, 0)} cm⁴</strong> and{" "}
            <strong style={{ color: C.teal }}>Z ≥ {fmt(res.Z_req, 0)} cm³</strong>.{" "}
            <strong style={{ color: res.governs === "deflection" ? C.amber : C.blue }}>
              {res.governs === "deflection" ? "Deflection" : "Strength"} governs
            </strong>{" "}
            ({fmt(Math.max(res.util_def, res.util_str) * 100, 0)}% utilised).{" "}
            {res.passes
              ? "Your current section passes both — the spare margin on the governing criterion is how far you could trim it."
              : "Your current section fails at least one limit — increase the property flagged red."}
          </p>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
        <button style={btnGhost} onClick={() => setTab("results")}>← Results</button>
        <button style={btnGhost} onClick={() => setTab("download")}>Download Notebook →</button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Practice tab — code editor + Run + Show solution. Self-contained state.
   ═══════════════════════════════════════════════════════════════════════════ */
function PracticeTab({ pyReady }) {
  const [exIdx, setExIdx] = useState(0);
  const [varIdx, setVarIdx] = useState(0);
  const [code, setCode] = useState(EXERCISES[0].starter);
  const [showSol, setShowSol] = useState(false);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);   // {out, err, figs}

  const ex = EXERCISES[exIdx];
  const variants = ex.variants || null;   // null for single-snippet exercises
  const activeStarter  = variants ? variants[varIdx].starter  : ex.starter;
  const activeSolution = variants ? variants[varIdx].solution : ex.solution;

  function pick(i) {
    const e = EXERCISES[i];
    setExIdx(i); setVarIdx(0);
    setCode(e.variants ? e.variants[0].starter : e.starter);
    setShowSol(false); setRes(null);
  }

  function pickVar(v) {
    setVarIdx(v); setCode(variants[v].starter);
    setShowSol(false); setRes(null);
  }

  async function run() {
    setBusy(true); setRes(null);
    try {
      const py = await getPyodide();
      py.globals.set("STUDENT_CODE", code);
      setRes(JSON.parse(py.runPython(PY_RUN_STUDENT)));
    } catch (e) {
      setRes({ out: "", err: String(e), figs: [] });
    } finally { setBusy(false); }
  }

  // Tab key inserts 4 spaces instead of leaving the textarea.
  function onKey(e) {
    if (e.key === "Tab") {
      e.preventDefault();
      const t = e.target, s = t.selectionStart, en = t.selectionEnd;
      const next = code.slice(0, s) + "    " + code.slice(en);
      setCode(next);
      requestAnimationFrame(() => { t.selectionStart = t.selectionEnd = s + 4; });
    }
  }

  const lastErr = res && res.err
    ? res.err.trim().split("\n").filter((l) => l.trim()).pop()
    : null;

  return (
    <div>
      <SectionHead>Practice — write &amp; run Python</SectionHead>

      <div style={{ background: C.navy, border: `1px solid ${C.navyBorder}`,
                    borderRadius: 8, padding: "12px 14px", fontSize: 13,
                    color: C.textMuted, marginBottom: 14, lineHeight: 1.6 }}>
        New to Python? You're in the right place. Work through the steps left to right —
        they get a little deeper each time. Replace each <code>___</code> blank, press{" "}
        <strong style={{ color: C.amber }}>▶ Run my code</strong>, and read what comes back.
        Stuck or curious? <strong style={{ color: C.teal }}>💡 Show solution</strong> is always
        there — reading worked code is part of learning, not cheating. Nothing you type can
        break anything, so experiment freely.
      </div>

      {/* Exercise selector */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
        {EXERCISES.map((e, i) => (
          <button key={e.id} onClick={() => pick(i)} style={{
            background: i === exIdx ? C.navyLight : "transparent",
            color: i === exIdx ? C.teal : C.textMuted,
            border: `1px solid ${i === exIdx ? C.teal : C.navyBorder}`,
            borderRadius: 6, padding: "6px 12px", fontFamily: "inherit",
            fontSize: 12, cursor: "pointer",
          }}>{e.title}</button>
        ))}
      </div>

      <p style={{ color: C.textPrimary, fontSize: 13, marginBottom: 8 }}>{ex.instructions}</p>
      <div style={{ background: C.navy, border: `1px solid ${C.navyBorder}`,
                    borderLeft: `3px solid ${C.amber}`, borderRadius: 6,
                    padding: "8px 12px", fontSize: 12, color: C.textMuted, marginBottom: 12 }}>
        🎯 Expected: <span style={{ color: C.textCode }}>{ex.expected}</span>
      </div>

      {/* Variant sub-tabs (e.g. Shear / Moment / Deflection) */}
      {variants && (
        <div style={{ display: "flex", gap: 0, marginBottom: 10,
                      borderBottom: `1px solid ${C.navyBorder}` }}>
          {variants.map((v, i) => (
            <button key={v.label} onClick={() => pickVar(i)} style={{
              background: "transparent", border: "none", cursor: "pointer",
              fontFamily: "inherit", fontSize: 12.5, padding: "8px 14px",
              color: i === varIdx ? C.teal : C.textMuted,
              borderBottom: `2px solid ${i === varIdx ? C.teal : "transparent"}`,
            }}>{v.label}</button>
          ))}
        </div>
      )}

      {/* Editor */}
      <textarea value={code} onChange={(e) => setCode(e.target.value)} onKeyDown={onKey}
                spellCheck={false}
                style={{
                  width: "100%", minHeight: 280, resize: "vertical",
                  background: "#0b121b", color: C.textCode, border: `1px solid ${C.navyBorder}`,
                  borderRadius: 8, padding: 12, fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 13, lineHeight: 1.5, tabSize: 4,
                }} />

      <div style={{ display: "flex", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
        <button style={{ ...btnPrimary, ...((!pyReady || busy) ? disabledBtn : {}) }}
                disabled={!pyReady || busy} onClick={run}>
          {busy ? "Running…" : "▶ Run my code"}
        </button>
        <button style={btnGhost} onClick={() => setCode(activeStarter)}>↺ Reset</button>
        <button style={btnGhost} onClick={() => setShowSol((s) => !s)}>
          {showSol ? "Hide solution" : "💡 Show solution"}
        </button>
      </div>

      {/* Output */}
      {res && (
        <div style={{ marginTop: 16 }}>
          {lastErr ? (
            <div>
              <div style={{ color: C.red, fontSize: 13, fontWeight: 700 }}>Error: {lastErr}</div>
              <details style={{ marginTop: 6 }}>
                <summary style={{ color: C.textMuted, fontSize: 12, cursor: "pointer" }}>
                  Full traceback
                </summary>
                <pre style={{ background: "#0b121b", border: `1px solid ${C.navyBorder}`,
                              borderRadius: 6, padding: 12, fontSize: 12, color: C.red,
                              overflowX: "auto", whiteSpace: "pre-wrap" }}>{res.err}</pre>
              </details>
            </div>
          ) : (
            <div>
              {res.out && (
                <pre style={{ background: "#0b121b", border: `1px solid ${C.navyBorder}`,
                              borderRadius: 6, padding: 12, fontSize: 12.5, color: C.textCode,
                              overflowX: "auto", whiteSpace: "pre-wrap" }}>{res.out}</pre>
              )}
              {res.figs.map((b, i) => (
                <img key={i} src={"data:image/png;base64," + b} alt="figure"
                     style={{ width: "100%", maxWidth: 720, borderRadius: 8, marginTop: 10,
                              border: `1px solid ${C.navyBorder}` }} />
              ))}
              {!res.out && res.figs.length === 0 && (
                <div style={{ color: C.amber, fontSize: 13 }}>
                  Ran with no output — did you forget a <code>print()</code>?
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {showSol && (
        <pre style={{ background: "#0b121b", border: `1px solid ${C.teal}`,
                      borderRadius: 8, padding: 12, fontSize: 13, color: C.textCode,
                      overflowX: "auto", whiteSpace: "pre-wrap", marginTop: 14 }}>{activeSolution}</pre>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main component.
   ═══════════════════════════════════════════════════════════════════════════ */
function BeamAnalysisTool() {
  // geometry
  const [L, setL] = useState(10);
  const [A, setA] = useState(2);
  const [B, setB] = useState(8);
  // section
  const [E, setE] = useState(200);     // GPa
  const [I, setI] = useState(8000);    // cm^4
  // loads
  const [P, setP] = useState(50);      // kN
  const [xP, setXP] = useState(5);     // m
  const [w, setW] = useState(10);      // kN/m
  // ui
  const [tab, setTab] = useState("geometry");
  const [pyReady, setPyReady] = useState(false);
  const [pyStatus, setPyStatus] = useState("loading");  // loading | idle | running | error
  const [running, setRunning] = useState(false);
  // results
  const [plot, setPlot] = useState(null);
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState(null);

  const model = { L, A, B, E, I, P, xP, w };

  /* Load Pyodide once on mount. */
  useEffect(() => {
    let alive = true;
    getPyodide()
      .then(() => { if (alive) { setPyReady(true); setPyStatus("idle"); } })
      .catch((e) => { if (alive) { setPyStatus("error"); setErr(String(e)); } });
    return () => { alive = false; };
  }, []);

  /* ── Constraint-enforcing setters (A < B-0.5, A+0.5 < B ≤ L) ──────────── */
  const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

  function changeL(v) {
    const nb = Math.min(B, v);
    const na = Math.min(A, nb - 0.5);
    setL(v); setB(nb); setA(Math.max(0, na));
    if (xP > v) setXP(v);
  }
  const changeA  = (v) => setA(clamp(v, 0, B - 0.5));
  const changeB  = (v) => setB(clamp(v, A + 0.5, L));
  const changeXP = (v) => setXP(clamp(v, 0, L));

  /* ── Run the full analysis (Results tab) ─────────────────────────────── */
  async function runAnalysis() {
    setRunning(true); setPyStatus("running"); setErr(null);
    try {
      const py = await getPyodide();
      setModel(py, model);
      const out = JSON.parse(py.runPython(PY_ANALYSIS));
      setStats(out.stats);
      setPlot("data:image/png;base64," + out.plot);
      setPyStatus("idle");
    } catch (e) { setErr(String(e)); setPyStatus("error"); }
    finally { setRunning(false); }
  }

  /* ── Download the generated notebook (Download tab) ──────────────────── */
  async function downloadNotebook() {
    const py = await getPyodide();
    setModel(py, model);
    const nb = py.runPython(PY_NOTEBOOK);
    const blob = new Blob([nb], { type: "application/x-ipynb+json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ssb_instrahub_L${L}_A${A}_B${B}.ipynb`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  /* ── Derived geometry ─────────────────────────────────────────────────── */
  const segLeft = A, segSpan = B - A, segRight = L - B;

  const dotColor = { loading: C.amber, idle: C.teal, running: C.amber, error: C.red }[pyStatus];
  const dotLabel = { loading: "Loading kernel…", idle: "Kernel ready",
                     running: "Running…", error: "Kernel error" }[pyStatus];

  const TABS = [
    ["geometry", "▲ Geometry"], ["loads", "⬇ Loads"], ["results", "📊 Results"],
    ["practice", "✏️ Practice"], ["optimise", "⚖ Optimise"], ["download", "⬇ Download Notebook"],
  ];

  const wrap = {
    fontFamily: "'JetBrains Mono', monospace", color: C.textPrimary,
    background: C.navyDeep, minHeight: "100%",
  };

  return (
    <div style={wrap}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        #beam-tool-root ::-webkit-scrollbar { height: 6px; }
        #beam-tool-root ::-webkit-scrollbar-thumb { background: ${C.navyBorder}; border-radius: 3px; }
      `}</style>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div style={{ background: C.navyDeep, borderBottom: `1px solid ${C.navyBorder}`,
                    padding: "14px 22px", display: "flex", justifyContent: "space-between",
                    alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted }}>InstraHub · Course Tool</div>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Simply Supported Beam Analysis</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12,
                      color: C.textMuted }}>
          <span style={{ width: 9, height: 9, borderRadius: "50%", background: dotColor,
                         display: "inline-block" }} />
          {dotLabel}
        </div>
      </div>

      {/* ── Tab bar ────────────────────────────────────────────────────── */}
      <div style={{ background: C.navyDeep, display: "flex", gap: 4, overflowX: "auto",
                    borderBottom: `1px solid ${C.navyBorder}`, padding: "0 12px" }}>
        {TABS.map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            background: "transparent", border: "none", cursor: "pointer",
            fontFamily: "inherit", fontSize: 13, padding: "12px 14px", whiteSpace: "nowrap",
            color: tab === id ? C.teal : C.textMuted,
            borderBottom: `2px solid ${tab === id ? C.teal : "transparent"}`,
          }}>{label}</button>
        ))}
      </div>

      {/* ── Body ───────────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 820, margin: "0 auto", padding: "22px" }}>

        {/* GEOMETRY ----------------------------------------------------- */}
        {tab === "geometry" && (
          <div>
            <SectionHead>Geometry</SectionHead>
            <SliderRow label="Total length L" value={L} unit="m" min={2} max={20} step={0.5}
                       onChange={changeL} />
            <SliderRow label="Pin A position" value={A} unit="m" min={0} max={B - 0.5} step={0.5}
                       onChange={changeA} />
            <SliderRow label="Roller B position" value={B} unit="m" min={A + 0.5} max={L} step={0.5}
                       onChange={changeB} />

            <table style={{ width: "100%", borderCollapse: "collapse", margin: "12px 0",
                            fontSize: 13 }}>
              <thead>
                <tr style={{ background: C.navy }}>
                  <th style={{ textAlign: "left", padding: "8px 12px",
                               borderLeft: `3px solid ${C.teal}`, color: C.textPrimary }}>Segment</th>
                  <th style={{ textAlign: "right", padding: "8px 12px",
                               color: C.textPrimary }}>Length</th>
                </tr>
              </thead>
              <tbody style={{ color: C.textCode }}>
                {[["Left cantilever", segLeft], ["Interior span", segSpan],
                  ["Right cantilever", segRight]].map(([n, v]) => (
                  <tr key={n} style={{ borderBottom: `1px solid ${C.navyBorder}` }}>
                    <td style={{ padding: "8px 12px" }}>{n}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(v, 2)} m</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <BeamDiagram L={L} A={A} B={B} P={0} xP={xP} w={0} />

            <button style={{ ...btnPrimary, marginTop: 14 }} onClick={() => setTab("loads")}>
              Next: Loads →
            </button>
          </div>
        )}

        {/* LOADS -------------------------------------------------------- */}
        {tab === "loads" && (
          <div>
            <SectionHead>Loads</SectionHead>
            <SliderRow label="Point load P" value={P} unit="kN" min={0} max={500} step={5}
                       onChange={setP} />
            <SliderRow label="Point load position x_P" value={xP} unit="m" min={0} max={L} step={0.5}
                       onChange={changeXP} />
            <SliderRow label="UDL w (full span)" value={w} unit="kN/m" min={0} max={100} step={1}
                       onChange={setW} />

            <SectionHead>Section (for deflection)</SectionHead>
            <SliderRow label="Young's modulus E" value={E} unit="GPa" min={10} max={400} step={5}
                       onChange={setE} />
            <SliderRow label="Second moment I" value={I} unit="cm⁴" min={500} max={50000} step={100}
                       onChange={setI} />

            <BeamDiagram L={L} A={A} B={B} P={P} xP={xP} w={w} />

            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <button style={btnGhost} onClick={() => setTab("geometry")}>← Geometry</button>
              <button style={btnPrimary}
                      onClick={() => { setTab("results"); runAnalysis(); }}>▶ Run Analysis →</button>
            </div>
          </div>
        )}

        {/* RESULTS ------------------------------------------------------ */}
        {tab === "results" && (
          <div>
            <SectionHead>Results</SectionHead>
            <button style={{ ...btnPrimary, ...((!pyReady || running) ? disabledBtn : {}) }}
                    disabled={!pyReady || running} onClick={runAnalysis}>
              {running ? "Running…" : (stats ? "↺ Re-run" : "Run Analysis")}
            </button>

            {err && <p style={{ color: C.red, fontSize: 13, marginTop: 12 }}>{err}</p>}

            {stats && (
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "18px 0" }}>
                <StatCard label="Reaction R_A" value={fmt(stats.RA)} unit="kN" color={C.teal} />
                <StatCard label="Reaction R_B" value={fmt(stats.RB)} unit="kN" color={C.teal} />
                <StatCard label="|M|max" value={fmt(stats.Mmax)} unit="kN·m" color={C.blue} />
                <StatCard label="|V|max" value={fmt(stats.Vmax)} unit="kN" color={C.blue} />
                <StatCard label="δmax" value={fmt(stats.dmax)} unit="mm" color={C.amber} />
              </div>
            )}

            {plot && (
              <img src={plot} alt="SFD / BMD / deflection"
                   style={{ width: "100%", maxWidth: 760, borderRadius: 8,
                            border: `1px solid ${C.navyBorder}` }} />
            )}

            <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
              <button style={btnGhost} onClick={() => setTab("loads")}>← Loads</button>
              <button style={btnGhost} onClick={() => setTab("optimise")}>Optimise →</button>
            </div>
          </div>
        )}

        {/* PRACTICE ----------------------------------------------------- */}
        {tab === "practice" && <PracticeTab pyReady={pyReady} />}

        {/* OPTIMISE ----------------------------------------------------- */}
        {tab === "optimise" && (
          <OptimiseTab model={model} pyReady={pyReady} setTab={setTab} />
        )}

        {/* DOWNLOAD ----------------------------------------------------- */}
        {tab === "download" && (
          <div>
            <SectionHead>Download notebook</SectionHead>
            <p style={{ color: C.textMuted, fontSize: 13, marginBottom: 12 }}>
              A self-contained Jupyter notebook with your current model baked in and the
              full analysis worked through in lesson order.
            </p>
            <table style={{ width: "100%", borderCollapse: "collapse", margin: "12px 0",
                            fontSize: 13 }}>
              <tbody style={{ color: C.textCode }}>
                {[["L", `${fmt(L, 1)} m`], ["Pin A", `${fmt(A, 1)} m`],
                  ["Roller B", `${fmt(B, 1)} m`], ["Point load P", `${P} kN @ ${fmt(xP, 1)} m`],
                  ["UDL w", `${w} kN/m`], ["E", `${E} GPa`], ["I", `${I} cm⁴`]].map(([k, v]) => (
                  <tr key={k} style={{ borderBottom: `1px solid ${C.navyBorder}` }}>
                    <td style={{ padding: "7px 12px", color: C.textMuted }}>{k}</td>
                    <td style={{ padding: "7px 12px", textAlign: "right" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button style={{ ...btnPrimary, ...((!pyReady) ? disabledBtn : {}) }}
                    disabled={!pyReady} onClick={downloadNotebook}>⬇ Download .ipynb</button>
            <div style={{ marginTop: 18 }}>
              <button style={btnGhost} onClick={() => setTab("optimise")}>← Optimise</button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

/* ── Mount ───────────────────────────────────────────────────────────────── */
ReactDOM.createRoot(document.getElementById("beam-tool-root")).render(<BeamAnalysisTool />);
