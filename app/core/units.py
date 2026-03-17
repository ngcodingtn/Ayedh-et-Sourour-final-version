"""Utilitaires de conversion d'unités.

Convention interne :
  - longueurs : mm
  - contraintes : MPa (N/mm²)
  - moments : N·mm
  - sections acier : mm²

Convention d'affichage UI :
  - longueurs : cm
  - moments : MN·m
  - sections acier : cm²
  - contraintes : MPa
"""
from __future__ import annotations


# ── Longueurs ────────────────────────────────────────
def m_to_mm(val: float) -> float:
    return val * 1_000.0

def mm_to_m(val: float) -> float:
    return val / 1_000.0

def cm_to_mm(val: float) -> float:
    return val * 10.0

def mm_to_cm(val: float) -> float:
    return val / 10.0

def cm_to_m(val: float) -> float:
    return val / 100.0

def m_to_cm(val: float) -> float:
    return val * 100.0


# ── Moments ──────────────────────────────────────────
def MNm_to_Nmm(val: float) -> float:
    """MN·m → N·mm"""
    return val * 1e9

def kNm_to_Nmm(val: float) -> float:
    """kN·m → N·mm"""
    return val * 1e6

def Nmm_to_kNm(val: float) -> float:
    """N·mm → kN·m"""
    return val / 1e6

def Nmm_to_MNm(val: float) -> float:
    """N·mm → MN·m"""
    return val / 1e9


# ── Sections ─────────────────────────────────────────
def mm2_to_cm2(val: float) -> float:
    return val / 100.0

def cm2_to_mm2(val: float) -> float:
    return val * 100.0


# ── Forces ───────────────────────────────────────────
def kN_to_N(val: float) -> float:
    return val * 1_000.0

def N_to_kN(val: float) -> float:
    return val / 1_000.0


# ── Formatage ────────────────────────────────────────
def fmt(val: float, decimales: int = 2) -> str:
    """Formate un nombre avec le nombre de décimales voulu."""
    return f"{val:.{decimales}f}"

def fmt_section_cm2(val_mm2: float, decimales: int = 2) -> str:
    """Formate une section mm² en cm²."""
    return f"{mm2_to_cm2(val_mm2):.{decimales}f} cm²"

def fmt_moment_kNm(val_Nmm: float, decimales: int = 2) -> str:
    """Formate un moment N·mm en kN·m."""
    return f"{Nmm_to_kNm(val_Nmm):.{decimales}f} kN·m"

def fmt_moment_MNm(val_Nmm: float, decimales: int = 4) -> str:
    """Formate un moment N·mm en MN·m."""
    return f"{Nmm_to_MNm(val_Nmm):.{decimales}f} MN·m"
