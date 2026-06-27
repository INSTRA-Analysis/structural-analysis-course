"""
beam_solver.py — Core solver for a simply supported beam with optional cantilevers.

Introduced in Lesson 5. Used in Lessons 6 and 7.

Beam layout:
    x=0 --[left cantilever]-- x_A --[interior span]-- x_B --[right cantilever]-- x=L
                               PIN                      ROLLER

Sign convention:
    - Downward forces (loads) : NEGATIVE
    - Upward forces (reactions): POSITIVE
    - Sagging bending moment  : POSITIVE
    - Hogging bending moment  : NEGATIVE

Public API
----------
  compute_reactions(geometry, loads)             → R_A, R_B
  compute_shear(geometry, loads, R_A, R_B)       → x, V
  compute_moments(x, V)                          → M
  analyse(geometry, loads)                       → {R_A, R_B, x, V, M}
  analyse_contributions(geometry, loads)         → above + per-load breakdown

The per-load layer (analyse_contributions) uses the direct section-cut method:
V and M at each point are computed analytically from each load's contribution,
then summed via superposition — exactly as done by hand.
"""

import numpy as np


def cumulative_trapezoid(y, x, initial=0.0):
    """
    Cumulative trapezoidal integral of y w.r.t. x, numpy-only.

    Drop-in for scipy.integrate.cumulative_trapezoid(y, x, initial=0.0):
    returns an array the same length as y, starting at `initial`.
    Implemented locally so this module (and the in-browser Pyodide build) has
    no scipy dependency — scipy is a very large WebAssembly download.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    out = np.empty_like(y)
    out[0] = initial
    out[1:] = initial + np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


# ---------------------------------------------------------------------------
# Reaction solver
# ---------------------------------------------------------------------------

def compute_reactions(geometry, loads):
    """
    Compute support reactions using static equilibrium.

    Parameters
    ----------
    geometry : dict  {"L_total": float, "x_A": float, "x_B": float}
    loads    : list of dicts, each with keys:
                 point load -> {"type": "point", "x": float, "magnitude": float}
                 UDL        -> {"type": "udl",   "x1": float, "x2": float, "w": float}

    Returns
    -------
    R_A, R_B : float, float   (positive = upward, in kN)
    """
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]
    span = x_B - x_A

    if span <= 0:
        raise ValueError("Right support (x_B) must be to the right of left support (x_A).")

    total_force = 0.0
    total_moment_about_A = 0.0

    for load in loads:
        if load["type"] == "point":
            P = load["magnitude"]
            x = load["x"]
            total_force += P
            total_moment_about_A += P * (x - x_A)

        elif load["type"] == "udl":
            w = load["w"]
            x1, x2 = load["x1"], load["x2"]
            if x2 <= x1:
                continue
            P_equiv = w * (x2 - x1)
            x_centroid = (x1 + x2) / 2.0
            total_force += P_equiv
            total_moment_about_A += P_equiv * (x_centroid - x_A)

    # ΣM about A = 0  →  R_B * span + total_moment_about_A = 0
    R_B = -total_moment_about_A / span
    # ΣFy = 0  →  R_A + R_B + total_force = 0
    R_A = -total_force - R_B

    return R_A, R_B


# ---------------------------------------------------------------------------
# Shear force
# ---------------------------------------------------------------------------

def compute_shear(geometry, loads, R_A, R_B, n_points=500):
    """
    Build the shear force array V(x) over the beam length.

    V at position x = sum of all vertical forces strictly to the LEFT of x
    (reactions are treated as upward point loads at x_A and x_B).

    Returns
    -------
    x_array : numpy array  shape (n_points,)
    V       : numpy array  shape (n_points,)  in kN
    """
    L = geometry["L_total"]
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]
    x_array = np.linspace(0.0, L, n_points)
    V = np.zeros(n_points)

    for i, xi in enumerate(x_array):
        v = 0.0
        # Reactions (upward = positive)
        if xi >= x_A:
            v += R_A
        if xi >= x_B:
            v += R_B
        # Applied loads
        for load in loads:
            if load["type"] == "point":
                if load["x"] <= xi:
                    v += load["magnitude"]
            elif load["type"] == "udl":
                x1, x2 = load["x1"], load["x2"]
                overlap_end = min(xi, x2)
                if overlap_end > x1:
                    v += load["w"] * (overlap_end - x1)
        V[i] = v

    return x_array, V


# ---------------------------------------------------------------------------
# Bending moment
# ---------------------------------------------------------------------------

def compute_moments(x_array, V):
    """
    Integrate shear force to obtain bending moment M(x).

    Uses the trapezoidal rule. M(0) = 0 (free left end).
    M[-1] should be ≈ 0 if the beam is in equilibrium.

    Returns
    -------
    M : numpy array  shape (n_points,)  in kN·m
    """
    M = cumulative_trapezoid(V, x_array, initial=0.0)
    return M


# ---------------------------------------------------------------------------
# Deflection (Euler–Bernoulli, double integration of M/EI)
# ---------------------------------------------------------------------------

def compute_deflection(x_array, M, EI, x_A, x_B):
    """
    Compute the transverse deflection δ(x) by double-integrating the
    moment–curvature relation, then enforcing the two support boundary
    conditions δ(x_A) = 0 and δ(x_B) = 0.

    Euler–Bernoulli small-deflection theory:
        d²δ/dx² = M(x) / EI            (curvature κ)
    Integrating once gives the slope, twice gives the deflection. The two
    constants of integration are fixed by the supports — here we apply them
    *after* the raw double integration by subtracting the unique straight
    line that makes δ vanish at both supports (valid because adding a linear
    function changes δ but not its curvature M/EI).

    Units — keep these consistent or the magnitude will be wrong
    -----------------------------------------------------------
        x_array : m
        M       : kN·m
        EI      : kN·m²
        → δ computed in m, returned in **mm** (× 1000).

    Convenience for the usual engineering inputs (E in GPa, I in cm⁴):
        1 GPa  = 1e6 kN/m²
        1 cm⁴  = 1e-8 m⁴
        ⇒ EI[kN·m²] = E[GPa] * I[cm⁴] * 1e-2

    Parameters
    ----------
    x_array : numpy array  shape (n,)   positions along the beam (m), increasing
    M       : numpy array  shape (n,)   bending moment (kN·m)
    EI      : float                     flexural rigidity (kN·m²), must be > 0
    x_A, x_B: float                     pin / roller positions (m), x_A < x_B

    Returns
    -------
    delta : numpy array  shape (n,)  deflection in mm
            (downward positive depends on the M sign convention; with the
             sagging-positive M used here, sagging curvature gives a
             downward sag between the supports as expected).

    Notes
    -----
    Deflection at the cantilever tips is a genuine extrapolation of the
    elastic curve and can be large — that is physically correct, not an error.
    """
    if EI <= 0:
        raise ValueError("EI must be positive (got %r)." % (EI,))
    if x_B <= x_A:
        raise ValueError("x_B must be greater than x_A.")

    # Curvature, then two successive trapezoidal integrations.
    kappa     = M / EI                                          # 1/m
    slope_raw = cumulative_trapezoid(kappa,     x_array, initial=0.0)
    defl_raw  = cumulative_trapezoid(slope_raw, x_array, initial=0.0)  # m

    # Raw deflection sampled exactly at the supports (linear interpolation
    # is more accurate than snapping to the nearest grid index).
    d_A = np.interp(x_A, x_array, defl_raw)
    d_B = np.interp(x_B, x_array, defl_raw)

    # Subtract the straight line through (x_A, d_A) and (x_B, d_B) so that the
    # corrected deflection is exactly zero at both supports.
    c0 = d_A
    c1 = (d_B - d_A) / (x_B - x_A)
    delta = defl_raw - (c0 + c1 * (x_array - x_A))             # m

    return delta * 1000.0                                      # → mm


# ---------------------------------------------------------------------------
# Convenience: run full analysis in one call
# ---------------------------------------------------------------------------

def analyse(geometry, loads, n_points=500):
    """
    Run the complete beam analysis.

    Returns
    -------
    results : dict with keys R_A, R_B, x, V, M
    """
    R_A, R_B = compute_reactions(geometry, loads)
    x, V = compute_shear(geometry, loads, R_A, R_B, n_points)
    M = compute_moments(x, V)
    return {"R_A": R_A, "R_B": R_B, "x": x, "V": V, "M": M}


# ---------------------------------------------------------------------------
# Per-load (superposition) layer — introduced alongside John's approach
# ---------------------------------------------------------------------------

def _load_label(load, index):
    """Return a human-readable string describing one load entry."""
    if load["type"] == "point":
        return f"Point {load['magnitude']:+.0f} kN @ x = {load['x']:.1f} m"
    elif load["type"] == "udl":
        return f"UDL {load['w']:+.1f} kN/m ({load['x1']:.1f}-{load['x2']:.1f} m)"
    return f"Load {index + 1}"


def _reaction_for_load(geometry, load):
    """
    Compute (R_A, R_B) due to a single load using moment equilibrium about A.

    This is the per-load equivalent of compute_reactions() — the foundation
    of the superposition approach.  Call for every load, then sum the results.

    Returns
    -------
    R_A_load, R_B_load : float  (positive = upward)
    """
    x_A  = geometry["x_A"]
    x_B  = geometry["x_B"]
    span = x_B - x_A

    if load["type"] == "point":
        P               = load["magnitude"]
        moment_about_A  = P * (load["x"] - x_A)
    elif load["type"] == "udl":
        w, x1, x2      = load["w"], load["x1"], load["x2"]
        P               = w * (x2 - x1)          # resultant of the UDL
        xc              = (x1 + x2) / 2.0         # centroid of the UDL block
        moment_about_A  = P * (xc - x_A)
    else:
        return 0.0, 0.0

    # ΣM_A = 0  →  R_B * span + moment_about_A = 0
    R_B = -moment_about_A / span
    # ΣFy = 0  →  R_A + R_B + P = 0
    R_A = -P - R_B
    return R_A, R_B


def _shear_for_load(geometry, load, R_A_load, R_B_load, x_array):
    """
    Build the shear force contribution V(x) for ONE load using the section-cut method:
    V at a cut x = sum of all vertical forces strictly to the LEFT.

    Vectorised over x_array — no Python loop needed.

    Returns
    -------
    V_load : numpy array  shape (len(x_array),)
    """
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]

    V = np.zeros(len(x_array))

    # Reactions act at their support positions
    V += R_A_load * (x_array >= x_A).astype(float)
    V += R_B_load * (x_array >= x_B).astype(float)

    if load["type"] == "point":
        V += load["magnitude"] * (x_array >= load["x"]).astype(float)

    elif load["type"] == "udl":
        x1, x2  = load["x1"], load["x2"]
        # Length of UDL seen from cut: min(xi, x2) - x1, clamped to ≥ 0
        overlap = np.maximum(np.minimum(x_array, x2) - x1, 0.0)
        V += load["w"] * overlap

    return V


def _moment_for_load(geometry, load, R_A_load, R_B_load, x_array):
    """
    Build the bending moment contribution M(x) for ONE load using the section-cut method:
    M at a cut x = sum of moments of all forces to the LEFT about the cut point.

    Sagging-positive convention:
        upward force F at position a  →  contributes +F*(x - a) for x > a
        downward load at position a   →  magnitude is negative, so contributes
                                          negative moment (hogging) ✓

    Vectorised over x_array — no Python loop needed.

    Returns
    -------
    M_load : numpy array  shape (len(x_array),)
    """
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]

    M = np.zeros(len(x_array))

    # Reactions
    M += R_A_load * np.maximum(x_array - x_A, 0.0)
    M += R_B_load * np.maximum(x_array - x_B, 0.0)

    if load["type"] == "point":
        xp = load["x"]
        M += load["magnitude"] * np.maximum(x_array - xp, 0.0)

    elif load["type"] == "udl":
        x1, x2 = load["x1"], load["x2"]
        # Right boundary of the loaded region seen from cut
        xc           = np.minimum(x_array, x2)
        length_loaded = np.maximum(xc - x1, 0.0)
        # Centroid of the loaded portion relative to the cut
        centroid     = (x1 + xc) / 2.0
        M += load["w"] * length_loaded * (x_array - centroid)
        # When length_loaded == 0 the whole term is 0, so no masking needed.

    return M


def analyse_contributions(geometry, loads, n_points=500):
    """
    Run the full beam analysis AND return the per-load contributions.

    This exposes the superposition principle explicitly: each load's effect on
    reactions, shear, and bending moment is computed separately using the
    section-cut method, then summed to give the total response.

    Parameters
    ----------
    geometry : dict   {"L_total": float, "x_A": float, "x_B": float}
    loads    : list of load dicts (same format as compute_reactions)
    n_points : int    resolution of the x-axis

    Returns
    -------
    dict with keys:
        "R_A"           : float   — total reaction at A
        "R_B"           : float   — total reaction at B
        "x"             : array   — x positions along the beam
        "V"             : array   — total shear force (superposition of all loads)
        "M"             : array   — total bending moment (superposition of all loads)
        "contributions" : list of dicts, one per load:
            {
              "label" : str    — human-readable description of this load
              "load"  : dict   — the original load dict
              "R_A"   : float  — reaction at A due to this load alone
              "R_B"   : float  — reaction at B due to this load alone
              "V"     : array  — shear contribution from this load
              "M"     : array  — moment contribution from this load
            }

    Usage example
    -------------
    result = analyse_contributions(geometry, loads)
    for c in result["contributions"]:
        print(c["label"], "  R_A =", c["R_A"])
    # Access totals:
    V_total = result["V"]
    M_total = result["M"]
    """
    x_array = np.linspace(0.0, geometry["L_total"], n_points)

    contributions = []
    R_A_total = 0.0
    R_B_total = 0.0
    V_total   = np.zeros(n_points)
    M_total   = np.zeros(n_points)

    for idx, load in enumerate(loads):
        R_A_load, R_B_load = _reaction_for_load(geometry, load)
        V_load = _shear_for_load(geometry, load, R_A_load, R_B_load, x_array)
        M_load = _moment_for_load(geometry, load, R_A_load, R_B_load, x_array)

        contributions.append({
            "label" : _load_label(load, idx),
            "load"  : load,
            "R_A"   : R_A_load,
            "R_B"   : R_B_load,
            "V"     : V_load,
            "M"     : M_load,
        })

        R_A_total += R_A_load
        R_B_total += R_B_load
        V_total   += V_load
        M_total   += M_load

    return {
        "R_A"           : R_A_total,
        "R_B"           : R_B_total,
        "x"             : x_array,
        "V"             : V_total,
        "M"             : M_total,
        "contributions" : contributions,
    }


# ---------------------------------------------------------------------------
# Self-check helper (useful in lessons)
# ---------------------------------------------------------------------------

def check_equilibrium(R_A, R_B, loads, tol=1e-3):
    """
    Verify that reactions balance all applied loads.
    Returns True if equilibrium is satisfied within tolerance.
    """
    total_load = 0.0
    for load in loads:
        if load["type"] == "point":
            total_load += load["magnitude"]
        elif load["type"] == "udl":
            total_load += load["w"] * (load["x2"] - load["x1"])
    residual = R_A + R_B + total_load
    return abs(residual) < tol
