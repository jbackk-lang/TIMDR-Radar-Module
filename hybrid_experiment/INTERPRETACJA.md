# Co pokazał pilot hybrydy radarowej

Na uproszczonym generatorze I/Q odzyskany zegar poprawił prognozę obwiedni przy liniowym przyspieszaniu, zwalnianiu i lukach. Estymacja widziała pierwsze 20 sekund, wynik liczono na ostatnich 10 sekundach. Każdy wiersz to średnia z pięciu niezależnych ziaren.

| Scenariusz | Stała częstotliwość | STFT + dryf | Zegar z astronomii | Znany zegar |
|---|---:|---:|---:|---:|
| Stały obrót | 0,201 | 0,366 | 0,220 | 0,199 |
| Przyspieszanie | 1,301 | 0,369 | **0,202** | 0,197 |
| Zwalnianie | 1,579 | 0,274 | **0,209** | 0,204 |
| Luki | 1,160 | 0,924 | **0,199** | 0,196 |

Wartości to **NMSE prognozy obwiedni: mniej = lepiej**, nie trafność klasyfikacji ani błąd położenia. Przy stałym obrocie prostsza metoda jest lepsza od odzyskanego zegara. Wszystkie pięć prób samego szumu otrzymało status unreliable. To zaledwie pięć prób negatywnych, nie oszacowanie niskiego odsetka fałszywych alarmów. Jeden przypadek zwalniania również oznaczono jako niewiarygodny; pozostał w tabeli.

W przypadku silnej drugiej harmonicznej zegar także uzyskał mały błąd, lecz **zakres częstotliwości początkowej 0,3–0,85 Hz wyklucza tu około dwukrotną częstotliwość startową**. Taka informacja wstępna pomaga rozstrzygać harmoniczne. Nie jest to dowód jednoznacznego odczytania fizycznego obrotu z błysków. Metody widmowe szukają pików w szerszym przedziale chwilowych częstotliwości 0,15–1,6 Hz; różnice w korzystaniu z informacji wstępnej ograniczają interpretację porównania.

Generator i estymator mają tę samą rodzinę fazy: częstotliwość zmienia się liniowo. Dlatego wynik wspiera **mechanizm wyrównania zegara przy zgodnym modelu**, nie dowodzi przewagi nad pełnym przetwarzaniem radarowym, dowolnym estymatorem chirpu ani na realnych pomiarach. Punkt ze znanym zegarem jest odniesieniem, a nie ścisłą granicą błędu w każdej realizacji szumu.

Trzy testy jednostkowe nowego modułu przeszły. Zapisane predykcje i metryki sprawdza verify.py. Historycznych testów pytest starego modułu nie powtórzono: w użytym środowisku brakuje pytest; stare pliki modelu nie były modyfikowane.

Najbliższy sensowny krok: zamrożony test z nieliniowym dryfem, zmiennymi amplitudami, aliasingiem i niezależnym modelem rozpraszania, następnie rzeczywiste I/Q. Dopiero potem ocena, czy cechy rotacyjne pomagają kojarzyć lub klasyfikować obiekty; poprawa pozycji wymaga osobnego eksperymentu.
