# TIMDR: pilot pola czas–częstotliwość

[Wynik i ograniczenia](WYNIK.md) · [Protokół](PROTOCOL.md) · [Porównanie](comparison.png)

Klasyczny algorytm śledzenia grzbietu widma jako eksperymentalny element projektu TIMDR. Z rzeczywistego widma Dopplera wyznacza prędkość radialną. Działa offline; nie mierzy obrotów, nie używa jeszcze zegara astronomicznego. Referencja w teście pochodzi z tego samego radaru. Dane: [Open Radar Initiative](https://github.com/openradarinitiative/open_radar_datasets), Gusland i in. 2021, CC BY-NC 4.0.

Z katalogu głównego repo:

```powershell
python -m pip install -r frequency_field_experiment/requirements.txt
python -m unittest discover -s frequency_field_experiment -p "test_*.py" -v
python frequency_field_experiment/verify.py
python frequency_field_experiment/benchmark.py --data "C:/Users/jback/Downloads/a/DATA/open_radar" --out frequency_field_experiment/results_rerun
```

Benchmark nie nadpisuje istniejących wyników. Cache dev/eval nie jest dołączony; `results/results.json` zawiera ścieżki i SHA-256 użytych plików. Weryfikacja hashy wejściowych wymaga tego samego lokalnego cache. `make_report.py` generuje raport z oryginalnego katalogu `results`.

API: `prepare(spec, times_s, frames, prf, fc)`, potem `ridge(*prepared, acceleration=10)`. `spec` ma kształt `(liczba klatek, liczba binów)` i oś częstotliwości z zerem pośrodku; czas w sekundach, PRF i częstotliwość nośna w Hz. Wyjście to m/s przy konwencji znaku osi wejściowego widma. `confidence` daje niekalibrowaną wyrazistość względem mediany mocy, nie prawdopodobieństwo poprawnego wyniku. Dane bez sygnału też mają matematycznego zwycięzcę — trzeba sprawdzić ten wskaźnik przed interpretacją.

Nie używać wyników tego eksperymentu do twierdzenia, że TIMDR jest szybszy od wszystkich innych metod: pole kosztuje więcej niż pojedynczy pik. Parametry wybierano tylko na dev, ale podstawowe wyniki eval były znane z wcześniejszego pilota, więc to badanie rozwojowe.

Dodatkowa diagnoza po głównym teście: `lag_diagnostic.py` sprawdza hipotezę stałego przesunięcia referencji dla dronów w zakresie ±0,20 s; wybiera na dev, ocenia na eval. Wybrano 0 s. Nie jest to pomiar opóźnienia GPS — zbiór nie daje tu niezależnej referencji GPS.
