# Pole czas–częstotliwość: wynik rozwojowego testu radarowego

**Średnia rozbieżność z prędkością podaną w zbiorze zmalała o 7.6%: z 1.701 do 1.571 m/s.** To dodatni wynik pilota, nie dowód przewagi całego TIMDR ani astronomicznej hybrydy.

## Dane i uczciwe odniesienie

[Open Radar Initiative](https://github.com/openradarinitiative/open_radar_datasets), Gusland i in. (2021), DOI 10.1109/RadarConf2147009.2021.9455239. Licencja danych CC BY-NC 4.0. Lokalne kopie rzeczywistych zespolonych widm, bez nowego pobierania. Użyto 210 śladów dev i 140 śladów eval (21 239 klatek). To wybrane wcześniej fragmenty, nie pełne nagrania zbioru.

Referencja jest pomiarem prędkości radialnej z **tego samego radaru**, nie niezależnym GPS. MAE oznacza zgodność z tą referencją. Nie badano pełnej prędkości przestrzennej ani obrotów. Dane eval były wcześniej użyte do porównania piku i mediany; nowy wybór parametrów korzystał wyłącznie z dev, ale wynik pozostaje eksploracyjny. Podział śladów nie gwarantuje niezależności sesji.

## Co robi pole częstotliwości

Widma tworzą pole czas × prędkość radialna. Algorytm wybiera do 16 lokalnych maksimów każdej klatki, a następnie znajduje przebieg o dużej mocy i małych zmianach prędkości. Kara za skok jest ograniczona, więc nie zabrania gwałtownych zmian. Nie łączy luk w danych. Jest to klasyczne programowanie dynamiczne, działające offline z dostępem do całego fragmentu.

TIMDR służy tutaj do organizacji modelu i sprawdzania hipotezy o spójności sygnału. Nie przypisujemy mu autorstwa Dopplera, FFT czy programowania dynamicznego. Nie użyto jeszcze astronomicznego zegara harmonicznego.

## Wyniki

MAE w m/s: najpierw średnia po klatkach każdego śladu, potem równa waga śladów. Wszystkie predykcje oceniono, także o małej wyrazistości widma.

| Grupa | Ślady | Pik | Filtr wykładniczy | Pole częstotliwości | Pole po przetasowaniu czasu |
|---|---:|---:|---:|---:|---:|
| bicycle | 19 | 0.834 | 0.839 | 0.750 | 0.831 |
| person | 21 | 0.457 | 0.460 | 0.425 | 0.429 |
| uav | 20 | 2.199 | 2.201 | 2.328 | 2.544 |
| vehicle | 80 | 2.108 | 2.111 | 1.878 | 2.257 |
| ALL | 140 | 1.701 | 1.704 | 1.571 | 1.830 |

Pole poprawiło 84 ślady, pogorszyło 56. Poprawa dotyczy średniej, nie każdego obiektu. **Drony wypadają gorzej.** Nie uruchamiano dodatkowego strojenia pod ich wynik.

Na dev wybrano skalę przyspieszenia 10 m/s² spośród 2, 10, 50; to parametr kary, nie oszacowane przyspieszenie obiektu. Filtr odniesienia wybrał alpha=0,8 spośród 0,2 / 0,5 / 0,8. Przetasowanie kolejności klatek niszczy korzyść pola: wynik 1.830 m/s. Wspiera to znaczenie kolejności czasowej, ale nie dowodzi mechanizmu fizycznego.

Przedział bootstrap 95% dla średniej poprawy względem piku: [0.035, 0.232] m/s, 2000 losowań śladów. To opisowa niepewność w tym cache; nie uwzględnia zależności między sesjami. Dodatkowy niesparowany Mann–Whitney po korekcie daje p=0.618, efekt rangowy 0.087; nie traktujemy go jako potwierdzenia przewagi.

## Koszt obliczeń

Wspólny etap przygotowania widm: 0.692 s. Czasy predykcji to suma median trzech powtórzeń na każdy ślad, po rozgrzewce, bez dysku:

- Pik: 0.0310 s.
- Filtr wykładniczy: 0.0743 s.
- Pole częstotliwości: 3.548 s, około 5986 klatek/s.

Pole jest około 114 razy wolniejsze niż sam pik w tej implementacji, choć bezwzględny koszt pozostaje mały. Przepustowość batch nie jest opóźnieniem systemu czasu rzeczywistego. Cały dobór i pomiar zajął 39.8 s. Nie porównywano czasu z siecią ani oryginalnym zegarem astronomicznym.

## Pliki i odtwarzanie

`frequency_field.py` — moduł; `test_frequency_field.py` — kontrole; `benchmark.py` — dobór i pomiar; `verify.py` — ponowne obliczenie metryk i sprawdzenie hashy. `results/` zawiera wszystkie predykcje, błędy, czasy, konfigurację zamrożoną przed eval i hashe wejść. Dane radarowe pozostają w zewnętrznym cache. Wykres `comparison.png` pokazuje wyniki; `examples.png` pokazuje pierwszy alfabetycznie ślad z każdej klasy, bez wybierania najładniejszych przypadków.

## Co dalej

Warto zachować pole jako opcjonalny moduł offline. Do oceny dronów potrzebne jest rozróżnienie odbić korpusu i wirnika; obecny algorytm nie identyfikuje ich fizycznie. Kolejny etap powinien używać nowych nagrań z niezależną prędkością i, dla astronomicznego zegara, znanymi obrotami. Tych etykiet nie tworzymy ze zgadywania lub z tego samego widma.

## Dodatkowa hipoteza: opóźnienie referencji dla dronów

Po głównym wyniku sprawdzono przesunięcia od -0,20 do +0,20 s co 0,05 s. Wybór na 30 śladach dev wskazał **0.00 s**, czyli brak przesunięcia. Osobny test 20 śladów eval na identycznych wewnętrznych klatkach (1164 klatki; brzegi odcięto dla wszystkich wariantów) daje pik 1.986 m/s i pole 2.115 m/s. Korekta wybrana na dev ich nie zmienia.

Nie znaleziono tu poparcia dla stałego opóźnienia w badanym zakresie; nie wyklucza to większego lub zmiennego opóźnienia. To nie test GPS: referencja jest radarowa. Przyczyna pogorszenia dronów pozostaje nieustalona. Zapis: `lag_diagnostic.py`, `results/lag_frozen.json`, `results/lag_diagnostic.json`. Ta diagnoza jest jawnie wykonana po poznaniu głównego wyniku, nie jest częścią pierwotnego protokołu.
