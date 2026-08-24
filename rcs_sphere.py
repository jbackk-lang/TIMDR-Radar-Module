"""
rcs_sphere.py — przekrój radarowy (RCS) idealnie przewodzącej kuli w
reżimie REZONANSOWYM (Mie), pełna seria Mie
================================================================================
UWAGA - TO JEST INNA FIZYKA NIŻ `ringdown_resonance()` (patrz ringdown.py
w TIMDR-Earthquake-Core i inne porty tej samej funkcji w tym projekcie).
`ringdown_resonance()` analizuje dogasanie sygnału W CZASIE po zdarzeniu
(tłumiony oscylator czasowy - np. własne "dzwonienie" przetwornika po
emisji impulsu). Ten moduł liczy co innego: jak przekrój radarowy celu
ZALEŻY OD CZĘSTOTLIWOŚCI/ROZMIARU celu względem długości fali - zjawisko
częstotliwościowe (rozpraszanie elektromagnetyczne), nie czasowe
dogasanie. Nie mylić tych dwóch znaczeń słowa "rezonans".

FIZYKA: rozpraszanie fali elektromagnetycznej na idealnie przewodzącej
(PEC) kuli ma dokładne rozwiązanie analityczne - szereg Mie (Gustav Mie,
1908). W zależności od parametru rozmiaru x = ka (k = 2π/λ, a = promień
kuli) wyróżnia się trzy reżimy, dobrze znane z każdego podręcznika
radarowego (np. Skolnik "Introduction to Radar Systems", Ruck "Radar
Cross Section Handbook", Balanis "Advanced Engineering Electromagnetics"):

  1. Reżim Rayleigha (x << 1, cel dużo mniejszy niż fala): σ ∝ λ⁻⁴ —
     to samo prawo, które tłumaczy błękit nieba (rozpraszanie Rayleigha).
  2. Reżim REZONANSOWY (x ~ 1, cel porównywalny z długością fali): σ
     OSCYLUJE z częstotliwością/rozmiarem wokół wartości optycznej,
     przez interferencję fali odbitej wprost i fal "pełzających"
     (creeping waves) okrążających kulę. Pierwszy, najsilniejszy pik
     (σ/πa² ≈ 3.6-3.7 przy x≈1) to klasyczny, wielokrotnie publikowany
     wynik.
  3. Reżim optyczny (x >> 1, cel dużo większy niż fala): σ → πa²
     (geometryczny przekrój kuli), z zanikającą oscylacją (ripple).

Ten moduł liczy DOKŁADNY (do zadanej liczby wyrazów szeregu, praktycznie
zbieżny) wynik dla kuli metodą Mie - kanoniczny, w pełni sprawdzalny
przypadek walidacyjny w elektromagnetyzmie/radarze (jest to STANDARDOWY
test poprawności każdego kodu liczącego RCS, dokładnie tak jak tłumiony
oscylator jest standardowym testem dla ringdown_resonance()).

**UCZCIWE OGRANICZENIE ZAKRESU (ważne, nie ukryte):** to rozwiązanie
JEST DOKŁADNE WYŁĄCZNIE DLA KULI. Dla dowolnego realnego celu (samolot,
statek, pojazd) reżim rezonansowy RCS wymaga pełnego rozwiązania
równań Maxwella dla tej konkretnej geometrii (metoda momentów MoM,
FEM, lub optyka fizyczna + fale pełzające dla ciał gładkich) - nie da
się tego uczciwie przybliżyć lekkim modułem Python bez solvera
elektromagnetycznego. Ten moduł NIE jest ogólnym narzędziem RCS dla
dowolnych kształtów - jest dokładnym rozwiązaniem dla jednego,
kanonicznego kształtu (kula), użytecznym jako: (a) walidacja/kalibracja
innych metod, (b) przybliżenie rzędu wielkości dla celów w przybliżeniu
kulistych (np. głowica, boja, balon), (c) ilustracja SAMEGO zjawiska
reżimu rezonansowego (żeby pokazać, że "rezonans" w RCS jest realny i
inny niż ringdown w czasie).

WALIDACJA (patrz test_rcs_sphere.py): trzy niezależne, dobrze znane
prawa fizyczne, każde sprawdzone numerycznie na WŁASNEJ implementacji
(nie przepisane z tabeli w podręczniku - wyprowadzone z definicji):
  1. Skalowanie Rayleigha: σ(2·ka)/σ(ka) → 2⁴=16 dla małych ka.
  2. Granica optyczna: σ/(πa²) → 1 dla dużych ka.
  3. Nie-monotoniczność (oscylacja) w reżimie rezonansowym ka∈[0.5,8] -
     odróżnia to jakościowo od prostego, monotonicznego wzrostu
     Rayleigha.
"""
from __future__ import annotations

import numpy as np
from scipy.special import spherical_jn, spherical_yn

SPEED_OF_LIGHT_M_S = 299_792_458.0


def _mie_coefficients(n: int, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Współczynniki Mie a_n, b_n dla idealnie przewodzącej (PEC) kuli,
    rząd n, parametr rozmiaru x=ka. Funkcje Riccatiego-Bessela
    zbudowane z funkcji sferycznych Bessela (scipy.special), zgodnie
    ze standardową definicją (np. Bowman/Senior/Uslenghi "Electromagnetic
    and Acoustic Scattering by Simple Shapes", Balanis "Advanced
    Engineering Electromagnetics")."""
    jn = spherical_jn(n, x)
    jnp = spherical_jn(n, x, derivative=True)
    yn = spherical_yn(n, x)
    ynp = spherical_yn(n, x, derivative=True)

    psi = x * jn
    psip = jn + x * jnp
    chi = -x * yn
    chip = -(yn + x * ynp)
    xi = psi - 1j * chi
    xip = psip - 1j * chip

    a_n = psip / xip
    b_n = psi / xi
    return a_n, b_n


def _n_terms_for_convergence(x: float) -> int:
    """Standardowa reguła obcięcia szeregu Mie (patrz Bohren & Huffman
    "Absorption and Scattering of Light by Small Particles", rozdz. 4.8;
    ta sama reguła jest uzywana w powszechnie stosowanych kodach Mie
    jak BHMIE/MIEV0): N = ceil(x + 4*x^(1/3) + 2), z minimum 5 wyrazow
    dla malych x (zeby reżim rezonansowy tez byl dobrze zbiezny)."""
    n = int(np.ceil(x + 4.0 * x ** (1.0 / 3.0) + 2))
    return max(n, 5)


def rcs_sphere_normalized(ka: float, n_terms: int | None = None) -> float:
    """Zwraca σ/(πa²) - znormalizowany monostatyczny (backscatter) RCS
    idealnie przewodzącej kuli, w funkcji parametru rozmiaru ka.
    Dokładny szereg Mie, obcięty przy n_terms (domyślnie: standardowa
    reguła zbieżności - patrz _n_terms_for_convergence)."""
    if ka <= 0:
        raise ValueError(f"ka musi być dodatnie, dostano {ka}")
    if n_terms is None:
        n_terms = _n_terms_for_convergence(ka)

    total = 0j
    for n in range(1, n_terms + 1):
        a_n, b_n = _mie_coefficients(n, ka)
        total += ((-1) ** n) * (2 * n + 1) * (a_n - b_n)

    # sigma = (lambda^2 / (4*pi)) * |sum|^2 = (pi/k^2) * |sum|^2
    # sigma / (pi*a^2) = |sum|^2 / (k*a)^2 = |sum|^2 / ka^2
    return float(np.abs(total) ** 2 / ka ** 2)


def rcs_sphere(frequency_hz: float, radius_m: float, n_terms: int | None = None) -> float:
    """Monostatyczny (backscatter) RCS [m²] idealnie przewodzącej kuli
    o promieniu `radius_m`, oświetlonej falą o częstotliwości
    `frequency_hz`. Dokładny szereg Mie (patrz docstring modułu po
    zakres ważności i walidację)."""
    if frequency_hz <= 0:
        raise ValueError(f"frequency_hz musi być dodatnie, dostano {frequency_hz}")
    if radius_m <= 0:
        raise ValueError(f"radius_m musi być dodatnie, dostano {radius_m}")
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    k = 2.0 * np.pi / wavelength_m
    ka = k * radius_m
    sigma_over_pia2 = rcs_sphere_normalized(ka, n_terms=n_terms)
    return sigma_over_pia2 * np.pi * radius_m ** 2


def sweep_rcs_vs_frequency(radius_m: float, freq_start_hz: float, freq_end_hz: float,
                            n_points: int = 200) -> dict:
    """Zwraca próbkowanie σ(f) [m²] i ka(f) w zadanym paśmie
    częstotliwości dla kuli o promieniu `radius_m` - wygodne do
    zobrazowania trzech reżimów (Rayleigh / rezonansowy / optyczny) na
    jednym wykresie."""
    freqs = np.linspace(freq_start_hz, freq_end_hz, n_points)
    wavelengths = SPEED_OF_LIGHT_M_S / freqs
    ka_values = 2.0 * np.pi * radius_m / wavelengths
    sigma = np.array([rcs_sphere(f, radius_m) for f in freqs])
    return {
        "frequency_hz": freqs,
        "ka": ka_values,
        "rcs_m2": sigma,
        "rcs_normalized": sigma / (np.pi * radius_m ** 2),
    }


def classify_regime(ka: float) -> str:
    """Zgrubna, powszechnie przyjęta klasyfikacja reżimu (progi
    orientacyjne, nie ostre granice fizyczne - w literaturze różne
    źródła podają nieco różne progi, np. Skolnik używa ka<1 (Rayleigh),
    1<ka<10 (rezonansowy/Mie), ka>10 (optyczny))."""
    if ka < 1.0:
        return "rayleigh"
    if ka <= 10.0:
        return "rezonansowy"
    return "optyczny"
