"""Generate a transparent result summary and reproducible, uncurated examples."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent

def main():
    r=json.loads((ROOT/'results/results.json').read_text(encoding='utf-8'))
    s=r['summary']; timing=r['prediction_seconds_sum_of_track_medians']; c=r['comparisons_vs_peak']['ridge']
    gain=100*(1-s['ALL']['mae']['ridge']/s['ALL']['mae']['peak'])
    table='\n'.join(f"| {cls} | {x['tracks']} | {x['mae']['peak']:.3f} | {x['mae']['exponential']:.3f} | {x['mae']['ridge']:.3f} | {x['mae']['shuffled_ridge']:.3f} |" for cls,x in s.items())
    txt=f'''# Pole czas–częstotliwość: wynik rozwojowego testu radarowego

**Średnia rozbieżność z prędkością podaną w zbiorze zmalała o {gain:.1f}%: z {s['ALL']['mae']['peak']:.3f} do {s['ALL']['mae']['ridge']:.3f} m/s.** To dodatni wynik pilota, nie dowód przewagi całego TIMDR ani astronomicznej hybrydy.

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
{table}

Pole poprawiło {c['tracks_better']} ślady, pogorszyło {c['tracks_worse']}. Poprawa dotyczy średniej, nie każdego obiektu. **Drony wypadają gorzej.** Nie uruchamiano dodatkowego strojenia pod ich wynik.

Na dev wybrano skalę przyspieszenia 10 m/s² spośród 2, 10, 50; to parametr kary, nie oszacowane przyspieszenie obiektu. Filtr odniesienia wybrał alpha=0,8 spośród 0,2 / 0,5 / 0,8. Przetasowanie kolejności klatek niszczy korzyść pola: wynik {s['ALL']['mae']['shuffled_ridge']:.3f} m/s. Wspiera to znaczenie kolejności czasowej, ale nie dowodzi mechanizmu fizycznego.

Przedział bootstrap 95% dla średniej poprawy względem piku: [{c['bootstrap95'][0]:.3f}, {c['bootstrap95'][1]:.3f}] m/s, 2000 losowań śladów. To opisowa niepewność w tym cache; nie uwzględnia zależności między sesjami. Dodatkowy niesparowany Mann–Whitney po korekcie daje p={c['p_bonferroni_descriptive']:.3f}, efekt rangowy {c['rank_biserial_descriptive']:.3f}; nie traktujemy go jako potwierdzenia przewagi.

## Koszt obliczeń

Wspólny etap przygotowania widm: {r['prepare_seconds']:.3f} s. Czasy predykcji to suma median trzech powtórzeń na każdy ślad, po rozgrzewce, bez dysku:

- Pik: {timing['peak']:.4f} s.
- Filtr wykładniczy: {timing['exponential']:.4f} s.
- Pole częstotliwości: {timing['ridge']:.3f} s, około {s['ALL']['frames']/timing['ridge']:.0f} klatek/s.

Pole jest około {timing['ridge']/timing['peak']:.0f} razy wolniejsze niż sam pik w tej implementacji, choć bezwzględny koszt pozostaje mały. Przepustowość batch nie jest opóźnieniem systemu czasu rzeczywistego. Cały dobór i pomiar zajął {r['elapsed_seconds']:.1f} s. Nie porównywano czasu z siecią ani oryginalnym zegarem astronomicznym.

## Pliki i odtwarzanie

`frequency_field.py` — moduł; `test_frequency_field.py` — kontrole; `benchmark.py` — dobór i pomiar; `verify.py` — ponowne obliczenie metryk i sprawdzenie hashy. `results/` zawiera wszystkie predykcje, błędy, czasy, konfigurację zamrożoną przed eval i hashe wejść. Dane radarowe pozostają w zewnętrznym cache. Wykres `comparison.png` pokazuje wyniki; `examples.png` pokazuje pierwszy alfabetycznie ślad z każdej klasy, bez wybierania najładniejszych przypadków.

## Co dalej

Warto zachować pole jako opcjonalny moduł offline. Do oceny dronów potrzebne jest rozróżnienie odbić korpusu i wirnika; obecny algorytm nie identyfikuje ich fizycznie. Kolejny etap powinien używać nowych nagrań z niezależną prędkością i, dla astronomicznego zegara, znanymi obrotami. Tych etykiet nie tworzymy ze zgadywania lub z tego samego widma.
'''
    lag_path=ROOT/'results/lag_diagnostic.json'
    if lag_path.exists():
        lag=json.loads(lag_path.read_text(encoding='utf-8'))
        txt+=f'''\n## Dodatkowa hipoteza: opóźnienie referencji dla dronów

Po głównym wyniku sprawdzono przesunięcia od -0,20 do +0,20 s co 0,05 s. Wybór na 30 śladach dev wskazał **{lag['selected_lag_seconds']:.2f} s**, czyli brak przesunięcia. Osobny test 20 śladów eval na identycznych wewnętrznych klatkach (1164 klatki; brzegi odcięto dla wszystkich wariantów) daje pik {lag['methods']['peak']['zero_lag_mae']:.3f} m/s i pole {lag['methods']['ridge']['zero_lag_mae']:.3f} m/s. Korekta wybrana na dev ich nie zmienia.

Nie znaleziono tu poparcia dla stałego opóźnienia w badanym zakresie; nie wyklucza to większego lub zmiennego opóźnienia. To nie test GPS: referencja jest radarowa. Przyczyna pogorszenia dronów pozostaje nieustalona. Zapis: `lag_diagnostic.py`, `results/lag_frozen.json`, `results/lag_diagnostic.json`. Ta diagnoza jest jawnie wykonana po poznaniu głównego wyniku, nie jest częścią pierwotnego protokołu.
'''
    (ROOT/'WYNIK.md').write_text(txt,encoding='utf-8')
    classes=list(s); x=np.arange(len(classes)); fig,ax=plt.subplots(figsize=(11,5))
    for j,(name,label) in enumerate([('peak','Doppler peak'),('exponential','Exponential filter'),('ridge','Frequency field'),('shuffled_ridge','Shuffled field')]):
        ax.bar(x+(j-1.5)*.19,[s[k]['mae'][name] for k in classes],.19,label=label)
    ax.set_xticks(x,classes); ax.set_ylabel('Track-macro MAE vs radar reference (m/s)')
    ax.set_title('Real radar: frequency-field pilot (not independent ground truth)'); ax.legend(); fig.tight_layout()
    fig.savefig(ROOT/'comparison.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    with np.load(ROOT/'results/predictions.npz') as z:
        for ax,cls in zip(axes.flat,[k for k in classes if k!='ALL']):
            row=next(row for row in r['tracks'] if row['class']==cls); key=row['track']
            t=z[key+'_time_seconds']; frames=z[key+'_frames']
            chunks=np.split(np.arange(len(t)),np.flatnonzero(np.diff(frames)!=1)+1)
            for name,label in [('reference','Radar reference'),('peak','Peak'),('ridge','Field')]:
                for j,ix in enumerate(chunks):
                    ax.plot(t[ix],z[key+'_'+name][ix],label=label if j==0 else None,
                      color={'reference':'black','peak':'#d78e25','ridge':'#157dac'}[name],alpha=.85,lw=1.2)
            ax.set_title(f'{cls}: {key} (first by filename)'); ax.set_xlabel('Time (s)'); ax.set_ylabel('Radial velocity (m/s)'); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(ROOT/'examples.png',dpi=160); plt.close(fig)

if __name__=='__main__': main()
