
# 📌 Binary Video Converter

Il modulo `binary_video_converter` permette di convertire un video normale in una versione **binarizzata** (bianco/nero), frame per frame.  
La binarizzazione può essere fatta in due modi:

* **Soglia globale** basata sulla **mediana** del frame (default)
* **Soglia adattiva** (`cv2.adaptiveThreshold`) utile con illuminazione irregolare

Il risultato è un nuovo video in scala di grigi (1 canale), salvato con **FFV1** (lossless) o **mp4v** (lossy).

Nella cartella `examples/data/` sono disponibili alcuni video di test (`tiny_video.mp4`, `tiny_video.avi`) utilizzabili direttamente negli esempi.


---

### ▶️ Utilizzo da terminale (CLI)

#### 1) Conversione semplice (soglia globale)

```bash
python scripts/binary_video_converter.py \
    --input examples/data/tiny_video.avi \
    --output output/tiny_video_binary.avi
````

#### 2) Conversione con ridimensionamento

```bash
python scripts/binary_video_converter.py \
    --input examples/data/tiny_video.mp4 \
    --output output/tiny_video_resized.avi \
    --width 320 --height 240
```

#### 3) Conversione con soglia adattiva

```bash
python scripts/binary_video_converter.py \
    --input examples/data/tiny_video.mp4 \
    --output output/tiny_video_adaptive.avi \
    --adaptive \
    --block 11 \
    --c 2
```

Parametri:

* `--block`: dimensione del blocco (deve essere **dispari**)
* `--c`: costante sottratta alla soglia locale

#### 4) Parametri completi disponibili

```bash
python scripts/binary_video_converter.py --help
```

Output sintetico:

```
--input / -i       Percorso video di input
--output / -o      Percorso video di output
--width / -W       Larghezza output (opzionale)
--height / -H      Altezza output (opzionale)
--init-frame       Frame da saltare all'inizio
--max-frame        Limite massimo di frame da processare
--lossy            Usa codec mp4v invece di FFV1
--adaptive         Attiva soglia adattiva
--block            Dimensione blocco (dispari)
--c                Costante soglia adattiva
--verbose          Livello messaggi (0, 1, 2...)
```

---

### ▶️ Utilizzo da Python

> **Nota sui notebook**
> Se il notebook si trova nella cartella `notebooks/`, i video nella cartella del progetto sono un livello sopra.
> Negli esempi seguenti si usa:
>
> ```python
> from pathlib import Path
> ROOT = Path().resolve().parents[0]         # sali dalla cartella notebooks/
> DATA_DIR = ROOT / "examples" / "data"      # video di esempio
> ```

---

#### 1) Conversione semplice

```python
from pathlib import Path
from motionpattern.binary_converter import binary_video_converter

ROOT = Path().resolve().parents[0]
DATA_DIR = ROOT / "examples" / "data"

binary_video_converter(
    input_path=DATA_DIR / "tiny_video.mp4",
    output_path=ROOT / "output" / "tiny_video_binary.avi",
    verbose=1
)
```

---

#### 2) Conversione con ridimensionamento

```python
binary_video_converter(
    input_path=DATA_DIR / "tiny_video.mp4",
    output_path=ROOT / "output" / "tiny_video_resized.avi",
    output_width=320,
    output_height=240,
    verbose=1,
)
```

---

#### 3) Conversione con soglia adattiva

```python
binary_video_converter(
    input_path=DATA_DIR / "tiny_video.mp4",
    output_path=ROOT / "output" / "tiny_video_adaptive.avi",
    adaptive=True,
    block_size=11,
    c=2,
    verbose=1,
)


