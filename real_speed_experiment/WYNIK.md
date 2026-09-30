# Prędkość na rzeczywistych sygnałach radarowych

Test wykonano 30.09.2026, bez ponownego pobierania danych i bez uczenia sieci. Przetwarzanie lokalnej pamięci danych trwało około 11 sekund.

Źródło: [Open Radar Initiative](https://github.com/openradarinitiative/open_radar_datasets), Gusland i in., 2021, DOI 10.1109/RadarConf2147009.2021.9455239. Dane CC BY-NC 4.0. Wykorzystano wcześniej zapisane zespolone widma rzeczywistych pomiarów; nie są to syntetyczne sygnały ani pełny zbiór surowych ADC.

## Co zmierzono

Prędkość radialną wyliczono z największego piku widma: v = c f_D / (2 f_c). Porównano ją z polem velocity dostarczonym przez autorów. To odniesienie z tego samego radaru, **nie niezależna prawda z GPS lub tachometru**. Rozbieżność nie oznacza automatycznie błędu naszej metody względem rzeczywistego ruchu.

Znak osi ustalono na 210 śladach dev. Wynik pochodzi z wszystkich 140 śladów eval dostępnych w lokalnym cache, 21 239 klatek. Zachowano istniejący podział; nie tworzono nowego losowania. Średnia jest liczona najpierw w obrębie śladu, potem między śladami.

| Obiekt | Ślady | Pik Dopplera: MAE m/s | Mediana 3 klatek: MAE m/s |
|---|---:|---:|---:|
| Rower | 19 | 0,834 | 0,841 |
| Człowiek | 21 | 0,457 | 0,482 |
| Dron | 20 | 2,199 | 2,286 |
| Pojazd | 80 | 2,108 | 2,096 |
| Wszystkie | 140 | 1,701 | 1,711 |

Mediana trzech klatek to tani, klasyczny test spójności czasowej. Nie łączy odległych fragmentów nagrania; korzysta także z sąsiedniej przyszłej klatki, więc jest wariantem offline. Nie jest astronomicznym estymatorem zegara ani nowym sitem TIMDR. Nie poprawiła wyniku ogólnego. Minimalna poprawa dla pojazdów nie wystarcza do stwierdzenia przewagi.

## Wniosek dla hybrydy

Mamy działającą ścieżkę od prawdziwego widma do prędkości w m/s i zapisane wyniki odniesienia. **Hybryda astronomiczna nie została tym testem zweryfikowana.** Częstość błysków odpowiada powtarzalności ruchu/obrotu, natomiast prędkość radialną mierzy przesunięcie Dopplera. Nie można podmienić jednej wielkości drugą. Kolejny sensowny test powinien sprawdzić, czy zegar obrotu pomaga odróżnić odbicia korpusu od wirujących części; potrzebuje też niezależnego odniesienia prędkości lub obrotów.

Odtwarzanie: uruchom test_speed.py w Pythonie z numpy i scipy. Domyślna lokalizacja danych to C:/Users/jback/Downloads/a/DATA/open_radar. Plik results.json zawiera protokół, metryki każdego śladu i SHA-256 wejść. predictions.npz zawiera predykcje i odniesienia. Nie kopiowano dużych plików pomiarowych ani nie zmieniano repozytorium.
