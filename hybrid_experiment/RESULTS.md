# Radar + zegar astronomiczny — wynik pilota

Wyłącznie symulacja obwiedni echa I/Q. Pięć ziaren na scenariusz. Estymacja na pierwszych 20 s, ocena na ostatnich 10 s. NMSE: mniej = lepiej; 1 odpowiada błędowi równemu wariancji testu. Nie jest to wynik śledzenia trajektorii ani fuzja kamery i radaru.

| Scenariusz | Stała częstotliwość | STFT + dryf | Zegar astronomiczny | Prawdziwy zegar | Akceptacje zegara |
|---|---:|---:|---:|---:|---:|
| Stały obrót | 0.201 | 0.366 | 0.220 | 0.199 | 5/5 |
| Przyspieszanie | 1.301 | 0.369 | 0.202 | 0.197 | 5/5 |
| Zwalnianie | 1.579 | 0.274 | 0.209 | 0.204 | 4/5 |
| Luki | 1.160 | 0.924 | 0.199 | 0.196 | 5/5 |
| Dwie podobne powierzchnie | 1.146 | 1.007 | 0.173 | 0.172 | 5/5 |
| Sam szum | 1.025 | 1.020 | 1.031 | — | 0/5 |

Wszystkie dopasowania, także oznaczone jako niewiarygodne, pozostają w tabeli. Nie wolno używać samego statusu accepted_model jako potwierdzenia fizycznej prędkości obrotu. W przypadku symetrii zegar może śledzić dwukrotną częstość błysków. Dla szumu brak fizycznej częstotliwości i punktu odniesienia oracle.

Generator ma liniowy dryf i stałe harmoniczne, zgodne z rodziną modelu astronomicznego. Wynik może wykazać przydatność tego założenia w kontrolowanym przykładzie, ale nie przewagę na rzeczywistym radarze. STFT jest jednym ustalonym punktem odniesienia, nie najlepszym możliwym estymatorem.

Kod estymatora skopiowano bez zmian z TIMDR-orbital-tracker/timdr_orbit/rotation_clock.py; pochodzenie i SHA-256: PROVENANCE.json. Sygnały I/Q, predykcje, parametry, przyczyny odrzucenia i metryki zapisano w results/. Nie zmieniono starego trackera ani modelu RCS kuli.