
# 📘 Sketch Generator

`SketchGenerator` ricostruisce un video mantenendo solo le regioni che corrispondono a una lista di pattern spaziotemporali.
Funziona su video **binarizzati** (pixel 0/255).

La finestra usata per generare i pattern ha dimensione:

- **spaziale**: `SpaceFilter × SpaceFilter`
- **temporale**: `TimeFilter` frame

Ogni finestra viene codificata in un intero; se l’intero è nella lista fornita, la regione originale viene copiata nello sketch.
Altrimenti lo sketch mostra un valore neutro.

---

## Requisiti

- video di input già binario → usare `binary_video_converter` prima dello sketch
- `TimeFilter * (SpaceFilter^2) ≤ 64` (pattern rappresentabili in 64 bit)
- lista di pattern = lista di interi già calcolati esternamente

---

## Uso in Python (singolo video)

> Nota sui notebook  
> Se il notebook si trova nella cartella `notebooks/`, la root del progetto è una cartella sopra:
>
> ```python
> from pathlib import Path
> ROOT = Path().resolve().parents[0]
> DATA_DIR = ROOT / "examples" / "data"
> ```

Esempio minimale su un singolo video binario:

```python
from pathlib import Path
from motionpattern.sketch_generator import SketchGenerator

ROOT = Path().resolve().parents[0]
DATA_DIR = ROOT / "examples" / "data"

patterns = [0, 123456, 789012]  # interi dei pattern ammessi

sk = SketchGenerator(
    path_in=DATA_DIR / "tiny_video_binary.avi",
    path_out=ROOT / "output" / "sketch.avi",
    list_patterns=patterns,
    TimeFilter=3,
    SpaceFilter=3,
)

stats = sk.generate(lossless=True, verbose=2)

print("ratio:", stats["ratio"])
print("frame_count:", stats["frame_count"])
print("pattern_totali:", stats["pattern_totali"])
print("pattern_accettati:", stats["pattern_accettati"])
````

Output:

* file video `sketch.avi`
* dizionario `stats` con le statistiche dell’elaborazione (vedi sotto)

---

## Valori di ritorno (`stats`)

La funzione `generate(...)` restituisce un dizionario:

```python
stats = {
    "ratio": float,              # pattern_accettati / pattern_totali
    "frame_count": int,          # numero di frame elaborati
    "pattern_totali": int,       # numero totale di pattern valutati
    "pattern_accettati": int,    # numero totale di pattern che matchano la lista
    "per_frame": list[dict],     # log per-frame
}
```

Ogni elemento di `stats["per_frame"]` è un dizionario:

```python
{
    "frame_index": int,         # indice del frame (0-based) nel loop di elaborazione
    "candidates_hash": int,     # numero di posizioni che passano il pre-filtraggio hash
    "accepted": int,            # numero di pattern accettati in quel frame
}
```

Esempio di analisi del log:

```python
import pandas as pd

df_log = pd.DataFrame(stats["per_frame"])
print(df_log.head())
```

---

## Parametri principali

| Parametro       | Descrizione                                                                        |
|-----------------|------------------------------------------------------------------------------------|
| `path_in`       | video binario di input                                                             |
| `path_out`      | file dello sketch                                                                  |
| `list_patterns` | lista di pattern ammessi (interi)                                                  |
| `TimeFilter`    | numero di frame nella finestra temporale                                           |
| `SpaceFilter`   | lato della finestra spaziale                                                       |
| `frame_rate`    | fps del video di output (None → usa input)                                         |
| `max_frame`     | numero massimo di frame da elaborare                                               |
| `verbose`       | livello di dettaglio nei messaggi (`0` nessuno, `1` base, `2` molto dettagliato)   |


---

## Codifica dei pattern

Lo SketchGenerator usa una codifica binaria interna:

```text
pattern = Σ pixel(bit) * 2^posizione
```

dove `posizione` dipende dalla posizione spaziale e dal frame nella finestra temporale.

I dettagli completi di codifica/decodifica sono gestiti dalle funzioni del modulo `pattern_encoding`.
Per usare `SketchGenerator` è sufficiente lavorare con le codifiche intere (`PatternValue`) prodotte dal resto della libreria.

---

## Pipeline tipica (singolo video)

1. Binarizza il video

   ```python
   from motionpattern.binary_converter import binary_video_converter

   binary_video_converter(
       input_path="input.avi",
       output_path="input_bin.avi",
   )
   ```

2. Carica o genera la lista di pattern (interi)
   (ad esempio a partire da una `PatternTable` con conteggi reali)

3. Genera lo sketch

   ```python
   sk = SketchGenerator(
       path_in="input_bin.avi",
       path_out="sketch.avi",
       list_patterns=patterns,
       TimeFilter=3,
       SpaceFilter=3,
   )

   stats = sk.generate(lossless=True, verbose=1)
   ```

---

## Esempio: sketch per tutti i video di una cartella

In questo esempio:

* usiamo una `PatternTable` con conteggi reali (`real_counting=True`)
* selezioniamo i pattern tramite l’euristica con `Max_W = 0.025` e `Max_N = 300`
* costruiamo la lista di pattern ammessi a partire da `PatternValue`
* generiamo lo sketch per **tutti** i file binari (`.avi`) in una cartella

```python
from pathlib import Path
from motionpattern.pattern_table import ImportData, apply_heuristic
from motionpattern.sketch_generator import SketchGenerator

# Notebook in notebooks/, root del progetto una cartella sopra
ROOT = Path().resolve().parents[0]
DATA_DIR = ROOT / "examples" / "data"

# Cartella con i video già binarizzati
INPUT_DIR = DATA_DIR / "binary_videos"
OUTPUT_DIR = ROOT / "output" / "sketches"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1) Importa la tabella dei pattern con conteggio reale
table = ImportData(
    path=DATA_DIR / "topk_riconteggio.csv",
    real_counting=True,
    TimeFilter=3,
    SpaceFilter=3,
)

# 2) Selezione dei pattern con euristica (Max_W = 0.025, Max_N = 300)
table_sel = apply_heuristic(
    df=table,
    Max_W=0.025,
    Max_N=300,
    inplace=False,
)

# 3) Lista di pattern ammessi: codifiche numeriche (PatternValue) dei selezionati
patterns = list(table_sel.get_PatternsValue(masked=True))

print(f"Pattern selezionati: {len(patterns)}")

# 4) Loop su tutti i video binari nella cartella
for path_in in INPUT_DIR.glob("*.avi"):
    path_out = OUTPUT_DIR / f"{path_in.stem}_sketch.avi"

    print(f"Elaboro: {path_in.name} → {path_out.name}")

    sk = SketchGenerator(
        path_in=path_in,
        path_out=path_out,
        list_patterns=patterns,
        TimeFilter=3,
        SpaceFilter=3,
    )

    stats = sk.generate(lossless=True, verbose=1)

    print("  ratio:", stats["ratio"])
    print("  pattern_totali:", stats["pattern_totali"])
    print("  pattern_accettati:", stats["pattern_accettati"])
```

In questo modo:

* la selezione dei pattern è controllata solo da `Max_W` e `Max_N` (euristica)
* la stessa lista di pattern viene riusata per tutti i video binari nella cartella
* per ogni video si ottiene uno sketch separato e un dizionario `stats` con le statistiche di elaborazione.

---

