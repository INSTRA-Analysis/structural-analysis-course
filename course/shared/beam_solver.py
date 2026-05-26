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
"""

import numpy as np
from scipy.integrate import cumulative_trapezoid


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
