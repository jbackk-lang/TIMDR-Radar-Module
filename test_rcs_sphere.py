"""Testy rcs_sphere.py - trzy niezależne, dobrze znane prawa fizyczne
rozpraszania elektromagnetycznego, każde sprawdzone na WŁASNEJ
implementacji szeregu Mie (nie przepisane z gotowej tabeli liczb)."""
import numpy as np
import pytest

from rcs_sphere import (
    rcs_sphere, rcs_sphere_normalized, sweep_rcs_vs_frequency, classify_regime,
    SPEED_OF_LIGHT_M_S,
)


def test_rayleigh_skalowanie_lambda_minus_4():
    """W reżimie Rayleigha (ka<<1) RCS skaluje się jak λ⁻⁴ ⟺ (ka)⁴ przy
    stałym promieniu - to samo prawo co rozpraszanie Rayleigha światła
    (dlaczego niebo jest niebieskie). Podwojenie ka powinno dać ~16x RCS."""
    ka_small, ka_double = 0.02, 0.04
    s_small = rcs_sphere_normalized(ka_small)
    s_double = rcs_sphere_normalized(ka_double)
    ratio = s_double / s_small
    assert ratio == pytest.approx(16.0, rel=0.01)


def test_rayleigh_jeszcze_mniejsze_ka_ratio_blizsze_16():
    """Kontrola: im mniejsze ka, tym bliżej dokładnego prawa (ka)^4 -
    (asymptotyczne prawo powinno być coraz dokladniejsze w granicy)."""
    ka1, ka2 = 0.005, 0.01
    ratio = rcs_sphere_normalized(ka2) / rcs_sphere_normalized(ka1)
    assert ratio == pytest.approx(16.0, rel=0.001)


def test_granica_optyczna_zbiega_do_przekroju_geometrycznego():
    """W reżimie optycznym (ka>>1) σ/(πa²) → 1 (geometryczny przekrój
    kuli) - fundamentalny, uniwersalnie znany wynik optyki geometrycznej."""
    for ka in [50, 80, 120, 200]:
        sigma_norm = rcs_sphere_normalized(ka)
        assert sigma_norm == pytest.approx(1.0, abs=0.05)


def test_reim_rezonansowy_jest_niemonotoniczny():
    """Odróznienie jakościowe od prostego wzrostu Rayleigha: w reżimie
    rezonansowym (ka~1-8) sygnał OSCYLUJE, nie rośnie/maleje monotonicznie."""
    ka_values = np.arange(0.5, 8.01, 0.25)
    sigma = np.array([rcs_sphere_normalized(ka) for ka in ka_values])
    diffs = np.diff(sigma)
    n_sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
    assert n_sign_changes >= 4  # kilka lokalnych ekstremow, nie 0-1


def test_pierwszy_pik_rezonansowy_w_znanym_zakresie():
    """Klasyczny, wielokrotnie publikowany wynik (np. Skolnik "Introduction
    to Radar Systems"): pierwszy, najsilniejszy pik σ/πa² dla kuli PEC
    wypada w poblizu ka≈1, z wartoscia rzedu 3-4 (nie ostra liczba w
    literaturze, ale rzad wielkosci jest dobrze ugruntowany)."""
    ka_values = np.arange(0.7, 1.3, 0.02)
    sigma = np.array([rcs_sphere_normalized(ka) for ka in ka_values])
    peak = np.max(sigma)
    assert 2.5 < peak < 5.0


def test_rcs_sphere_wymiary_fizyczne_m2():
    """rcs_sphere() zwraca RCS w m^2 - sprawdz przez porownanie z
    rcs_sphere_normalized() * pi * a^2."""
    freq = 3e9  # 3 GHz, pasmo S (typowy radar nadzoru)
    radius = 0.5  # m
    wavelength = SPEED_OF_LIGHT_M_S / freq
    ka = 2 * np.pi * radius / wavelength
    expected = rcs_sphere_normalized(ka) * np.pi * radius ** 2
    assert rcs_sphere(freq, radius) == pytest.approx(expected, rel=1e-9)


def test_odrzuca_nieprawidlowe_wejscie():
    with pytest.raises(ValueError):
        rcs_sphere(-1.0, 0.5)
    with pytest.raises(ValueError):
        rcs_sphere(1e9, -0.5)
    with pytest.raises(ValueError):
        rcs_sphere_normalized(0.0)


def test_sweep_rcs_vs_frequency_ksztalt_wyjscia():
    result = sweep_rcs_vs_frequency(radius_m=0.3, freq_start_hz=1e8, freq_end_hz=1e10, n_points=50)
    assert len(result["frequency_hz"]) == 50
    assert len(result["ka"]) == 50
    assert len(result["rcs_m2"]) == 50
    assert np.all(result["rcs_m2"] > 0)
    # ka rosnie monotonicznie z czestotliwoscia (promien staly)
    assert np.all(np.diff(result["ka"]) > 0)


def test_classify_regime_progi():
    assert classify_regime(0.5) == "rayleigh"
    assert classify_regime(5.0) == "rezonansowy"
    assert classify_regime(50.0) == "optyczny"


def test_wieksza_kula_ma_wieksze_rcs_w_reimie_optycznym():
    """Sanity check niezalezny od wyprowadzenia: w reżimie optycznym
    RCS ~ pi*a^2, wiec 2x promien -> ~4x RCS."""
    freq = 10e9  # 10 GHz, ka duze dla obu promieni ponizej
    r1, r2 = 2.0, 4.0
    s1 = rcs_sphere(freq, r1)
    s2 = rcs_sphere(freq, r2)
    assert s2 / s1 == pytest.approx(4.0, rel=0.1)
