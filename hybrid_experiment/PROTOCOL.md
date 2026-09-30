# Radar + zegar astronomiczny: tani pilot
Zapisano przed wynikami, 2026-09-30. Lokalny protokół, nie zewnętrzna prerejestracja.

Cel: oszacowanie zmiennej częstotliwości rotacyjnej i prognoza obwiedni echa na niewidzianym ostatnim 1/3 nagrania. Nie mierzymy prędkości lotu, AUC klasyfikacji ani błędu trajektorii.

Syntetyczny zespolony sygnał I/Q: amplituda z pierwszą i drugą harmoniczną rotacji, faza z Dopplerem ruchu całego obiektu i sinusoidalną modulacją mikroruchu. To uproszczony generator punktowy, nie pełny symulator elektromagnetyczny ani model RCS kuli. Wszystkie estymatory dostają tę samą obwiednię |I/Q|. Nie ma optycznego sensora ani fuzji niezależnych pomiarów. Sprawdzamy przeniesienie estymatora z astronomii.

30 sekund, 40 Hz; pierwsze 20 sekund: estymacja, ostatnie 10 sekund: zamknięta ocena. Sześć scenariuszy x pięć ziaren: obrót stały, przyspieszanie, zwalnianie, luki, dominująca druga harmoniczna (symetria), sam szum. Bez dostrajania po wyniku. Generator z liniowym dryfem jest zgodny z rodziną modelu zegara; to kontrolowany test mechanizmu, nie generalizacji na rzeczywistych obiektach.

Metody: klasyczna stała częstotliwość z okresogramu Lomb–Scargle; grzbiet STFT z liniową ekstrapolacją częstotliwości (tylko regularne wejście, luki interpolowane jawnie); oryginalny fit_clock z astronomy_clock.py; prawdziwy zegar generatora (górny punkt odniesienia, nie wykonalny konkurent). Każda metoda dopasowuje te same dwie harmoniczne i trend na treningu, następnie przewiduje obwiednię w teście. Estymatory nie widzą fazy ani częstotliwości generatora. Znane przedziały: f0 0.3–0.85 Hz, dryf -0.015–0.025 Hz/s, obserwowane częstotliwości 0.15–1.6 Hz dla metod widmowych. To informacja wstępna, nie estymacja bez ograniczeń.

Metryki: MAE częstotliwości fizycznego obrotu na końcowych 10 sekundach, NMSE prognozy obwiedni względem wariancji części testowej. Raportujemy także odsetek accepted_model oraz wyniki odrzuconych dopasowań; nie odrzucamy ich z zestawienia. Dla szumu nie istnieje prawdziwa częstotliwość/oracle. W przypadku symetrii raportujemy pomyłki harmoniczne, nie utożsamiamy częstości błysków z obrotem fizycznym. Pięć ziaren to rozpoznanie, nie mocny test istotności.

Hipoteza mechaniczna: prawdziwy zegar obniża NMSE względem częstotliwości stałej przy dryfie. Hipoteza praktyczna: zegar odzyskany z echa zbliża się do tego wyniku i poprawia wynik względem STFT. Negatywne wyniki i fałszywe akceptacje zachowujemy. Następny test musi objąć odmienny generator lub niezależne dane rzeczywiste.
