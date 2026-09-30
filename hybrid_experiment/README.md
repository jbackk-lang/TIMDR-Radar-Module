# Hybryda: radarowy sygnał + zegar z astronomii

**Działający pilot syntetyczny, 30 prób.** [Wyniki](RESULTS.md), [interpretacja](INTERPRETACJA.md), [protokół](PROTOCOL.md).

Uruchomienie z głównego katalogu repo:

```powershell
python -m pip install -r hybrid_experiment/requirements.txt
python -m unittest discover -s hybrid_experiment -p test_hybrid.py
python hybrid_experiment/run.py
python hybrid_experiment/verify.py
```

Istniejące wyniki są wznawiane po sprawdzeniu hasha protokołu. Zmiany modelu lub protokołu wymagają osobnego katalogu wyników. Bez uczenia sieci, płatnych API i pobierania danych. Czas zależy od procesora.

Kod w astronomy_clock.py to niezmieniona kopia lokalnego estymatora z TIMDR-orbital-tracker. PROVENANCE.json zapisuje źródło i SHA-256. Rola TIMDR: konstrukcja modelu, wybór zegara i porównania. Optymalizacja, analiza harmoniczna, STFT oraz modelowanie Dopplera są klasycznymi narzędziami.

W tym doświadczeniu nie poprawiano trajektorii timdr_radar.py, nie używano modelu rcs_sphere.py ani nie odczytywano prędkości lotu z jasności. Nie połączono danych kamery i radaru: sprawdzono przeniesienie estymatora zegara na radarową obwiednię. Wszystkie dopasowania i porażki są zapisane w results, także jeden odrzucony przypadek zwalniania.
