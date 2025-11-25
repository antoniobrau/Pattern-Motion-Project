# 📘 Spezzetta Sketch

La funzione `spezzetta_sketch` prende una coppia di video per ogni “id”:

- un **video binarizzato** completo, cioè il video originale dopo la binarizzazione (0/255)
- il relativo **video sketch** completo, cioè lo stesso video filtrato con un certo insieme di pattern

e per ciascuna coppia genera **due nuovi video più corti**:

- una clip **digitalized** (binarizzata) con una finestra temporale più larga
- una clip **sketch** con solo la finestra centrale

L’idea è costruire un dataset di clip allineate, dove per ogni spezzone hai:

- il video “digitale” (tutto ciò che è accaduto nella finestra larga)
- il relativo sketch (solo ciò che è stato selezionato dai pattern nella finestra centrale)

---

## 🧩 Idea generale

Per ogni video scegliamo una finestra temporale singola:

```text
digitalized: [ -- extra -- |  sketch_window  | -- extra -- ]
sketch:               [     sketch_window    ]
````

Parametri principali:

* `len_sketch`: numero di frame della finestra centrale (`sketch_window`)
* `extra`: quanti frame aggiungere prima e dopo nella parte digitalized
* `padding`: quanti frame neutri (grigio) aggiungere all’inizio e alla fine dei video spezzati
* `seed`: rende ripetibile la scelta casuale della finestra

Si assume che:

* esista **un video bin completo** con prefisso `bin_prefix`
* esista **un video sketch completo** corrispondente con prefisso `sketch_prefix`
* entrambi i file condividano lo stesso identificatore finale (es. `_123.avi`)

Se i prefissi non corrispondono ai file reali, basta modificarli nel blocco dei path.

La funzione controlla che ogni bin abbia lo sketch corrispondente e viceversa; se qualcosa non combacia, viene sollevato un errore con l’elenco degli id mancanti.

---

## 📁 Cartelle coinvolte

Tipicamente si usano quattro cartelle:

* `folder_bin`
  contiene i **video binarizzati completi** (un file per id), ad esempio:
  `BIN_001.avi`, `BIN_002.avi`, …

* `folder_sketch`
  contiene i **video sketch completi** ottenuti applicando uno specifico insieme di pattern, ad esempio:
  `STATICI_50_0.025_001.avi`, `STATICI_50_0.025_002.avi`, …

* `out_folder_bin`
  conterrà i **video digitalized spezzati**, uno per ogni id, ad esempio:
  `Digitalized_STATICI_50_0.025_001.avi`, …

* `out_folder_sketch`
  conterrà i **video sketch spezzati** allineati alle clip digitalizzate, ad esempio:
  `Sketch_STATICI_50_0.025_001.avi`, …

Le cartelle di output vengono create automaticamente se non esistono; i nomi reali possono essere cambiati a seconda dell’esperimento, basta aggiornare i path e i prefissi nello script.

```
```

---

## Requisiti

- video **binarizzati** (grayscale 0/255)
- video **sketch** generati dallo `SketchGenerator`
- stesso numero di frame o differenza minima (usa il minimo)
- nomi coerenti tramite `bin_prefix` e `sketch_prefix`

---

## 🧪 Uso in Python — Esempio minimo

> Nota sui notebook  
> Se il notebook è dentro `notebooks/`, la root è una cartella sopra:
>
> ```python
> from pathlib import Path
> ROOT = Path().resolve().parents[0]
> ```

```python
from pathlib import Path
from motionpattern.spezzetta_sketch import spezzetta_sketch

ROOT = Path().resolve().parents[0]

folder_bin = ROOT / "data" / "video_bin"
folder_sketch = ROOT / "data" / "video_sketch"
out_bin = ROOT / "data" / "spezzati_bin"
out_sketch = ROOT / "data" / "spezzati_sketch"

spezzetta_sketch(
    folder_bin=folder_bin,
    folder_sketch=folder_sketch,
    out_folder_bin=out_bin,
    out_folder_sketch=out_sketch,
    bin_prefix="BIN_",
    sketch_prefix="SK_",
    out_bin_prefix="Digitalized_",
    out_sketch_prefix="Sketch_",
    len_sketch=3,
    extra=2,
    padding=15,
    seed=42,
)
````

---

## 📁 Casi d’uso consigliati

### 1) Video singolo (debug o test rapido)

```python
spezzetta_sketch(
    folder_bin=folder_bin,           # contiene 1 solo BIN
    folder_sketch=folder_sketch,     # contiene 1 solo SK
    out_folder_bin=out_bin,
    out_folder_sketch=out_sketch,
    bin_prefix="",          
    sketch_prefix="SPATEMP_300_0.025_",
    out_bin_prefix="Digital_300_",
    out_sketch_prefix="Sketch_300_",
    len_sketch=3,
    extra=2,
)
```

---

### 2) Dataset intero (tutti i file di una cartella)

Questo è il caso tipico.

> Devi solo modificare le **3 cartelle** e i **prefissi**.
> Tutto il resto può rimanere invariato.

```python
from pathlib import Path
from motionpattern.spezzetta_sketch import spezzetta_sketch

base = Path(r"C:\Users\...\DATASET_RIPULITO")

folder_bin = base / "VIDEO_BINARIZZATI"
folder_sketch = base / "VIDEO_PATTERN_NON_OTTIMALI" / "STATICI_50_0.025"

out_folder_bin = base / "VIDEO_SPEZZATI" / "NON_OTTIMALI" / "DIGITALIZED_50_0.025"
out_folder_sketch = base / "VIDEO_SPEZZATI" / "NON_OTTIMALI" / "SKETCH_50_0.025"

spezzetta_sketch(
    folder_bin=folder_bin,
    folder_sketch=folder_sketch,
    out_folder_bin=out_folder_bin,
    out_folder_sketch=out_folder_sketch,
    bin_prefix="",                     
    sketch_prefix="STATICI_50_0.025_",  
    out_bin_prefix="Digitalized_STATICI_50_0.025_",
    out_sketch_prefix="Sketch_STATICI_50_0.025_",
    len_sketch=3,
    extra=2,
    padding=15,
    seed=42,
)
```

---

## 🎛️ Parametri principali

| Parametro           | Significato                                 |
| ------------------- | ------------------------------------------- |
| `folder_bin`        | cartella con i video binarizzati completi   |
| `folder_sketch`     | cartella con gli sketch completi            |
| `out_folder_bin`    | output delle clip “digitalized”             |
| `out_folder_sketch` | output delle clip sketch                    |
| `bin_prefix`        | prefisso dei video bin (es. `"BIN_"`)       |
| `sketch_prefix`     | prefisso dei video sketch (es. `"SKETCH_"`) |
| `out_bin_prefix`    | prefisso per i digitalized spezzati         |
| `out_sketch_prefix` | prefisso per gli sketch spezzati            |
| `len_sketch`        | lunghezza del blocco centrale               |
| `extra`             | frame extra a sinistra e destra             |
| `padding`           | frame neutri all’inizio/fine                |
| `codec`             | `"FFV1"` (lossless) o `"mp4v"`              |
| `seed`              | controlla la randomizzazione della finestra |

---

## ✏️ Come funziona l’allineamento dei file

La funzione assume che i nomi siano del tipo:

```
BIN_123.avi
SKETCH_123.avi
```

quindi estrae l’ID finale (`123`) e verifica che:

* ogni BIN abbia lo SK corrispondente
* ogni SK abbia il BIN corrispondente

Se qualcosa non combacia, viene mostrato un errore esplicito.

*Non serve altro: è tutto automatico.*

---

## 📦 Output finale

Per ogni video di input verranno generati due file:

```
[out_bin_prefix]<id>.avi
[out_sketch_prefix]<id>.avi
```

contenenti rispettivamente:

* **Digitalized**: finestra larga (extra + sketch + extra)
* **Sketch**: solo finestra centrale
* padding ai bordi per uniformare la lunghezza

---

