
# 📊 Importare e manipolare i pattern

Questo file spiega:

- come importare i file `.csv` in una tabella di pattern
- quali metodi base sono disponibili per analizzare la tabella
- come funzionano le funzioni di selezione (che aggiornano la colonna `Mask`)
- come usare la misura di dinamicità temporale (`Velocity`)

L’ingresso ai dati è la funzione:

```python
from motionpattern.pattern_table import ImportData
````

`ImportData` legge un file `.csv` di pattern e restituisce una tabella di lavoro (PatternTable) su cui poi si possono applicare metodi e funzioni di selezione.

---

## 1. Import dei dati

### 1.1. Impostare la cartella dei dati a partire da `notebooks/`

Negli esempi si assume di lavorare dentro la cartella `notebooks/`.
Per riferirsi ai dati nella cartella del progetto si usa:

```python
from pathlib import Path

# Siamo in notebooks/, saliamo di un livello per arrivare alla root del progetto
ROOT = Path().resolve().parents[0]
DATA_DIR = ROOT / "examples" / "data"
```

Da questo momento in poi i file di dati verranno letti come:

```python
path = DATA_DIR / "nome_file.csv"
```

---

### 1.2. Caso A – Conteggio reale (`real_counting=True`)

Questo è il caso in cui il file contiene già le probabilità dei pattern.

Requisiti del file:

* formato `.csv` con separatore `;`
* la riga di intestazione deve contenere almeno:

  ```text
  Pattern;p
  ```

  dove:

  * `Pattern` è la codifica binaria del pattern (come numero o stringa, gestita internamente)
  * `p` è la probabilità del pattern

Uso tipico (pattern spaziotemporali 3×3×3):

```python
from motionpattern.pattern_table import ImportData

table_3d = ImportData(
    path=DATA_DIR / "topk_riconteggio.csv",
    real_counting=True,
    TimeFilter=3,
    SpaceFilter=3,
)

table_3d.print_info(masked=True)
```

Uso per pattern statici 3×3 (nessuna dimensione temporale):

```python
table_static = ImportData(
    path=DATA_DIR / "pattern_statici_DelViva.csv",
    real_counting=True,
    TimeFilter=1,   # pattern statici
    SpaceFilter=3,  # patch 3x3
)

table_static.print_info(masked=True)
```

---

### 1.3. Caso B – Output dell’algoritmo (`real_counting=False`)

In questo caso il file è l’output dell’Floating Topk.
Il file:

* è sempre `.csv` con separatore `;`
* contiene alcune righe iniziali commentate con i parametri globali
* contiene colonne come `Sum_level`, `Count_level`, `Pattern`, …

`ImportData`:

* legge i parametri dall’header
* stima le probabilità `p` a partire dai livelli
* costruisce la tabella di pattern con le colonne standard

Esempio:

```python
table_algo = ImportData(
    path=DATA_DIR / "topk.csv",
    real_counting=False,
    p=0.999,   # parametro usato nella stima della probabilità
)

table_algo.print_info(masked=True)
```

È possibile specificare anche `TimeFilter` e `SpaceFilter`; se non coincidono con quelli dell’header viene generato un errore.

---

## 2. PatternTable: struttura e metodi base

Dopo la chiamata a `ImportData`, il risultato è una **tabella di pattern** che chiameremo sempre `table` (oggetto `PatternTable`).
È una tabella con alcune colonne standard già presenti.

Le colonne principali sono:

* `p` – probabilità del pattern
* `Entropy` – contributo di entropia del pattern
* `EntropyRatio` – contributo relativo rispetto alla somma totale
* `TimeFilter`, `SpaceFilter` – dimensione temporale e spaziale
* `PatternValue` – codifica numerica del pattern (usata come indice)
* `Pattern` – codifica numerica del pattern (non è usata come indice)
* `Mask` – indica se il pattern è attualmente selezionato (`True`/`False`)

La colonna chiave per la selezione è **`Mask`**:
tutte le funzioni successive lavorano cambiando `Mask` senza cancellare righe.

I metodi di `PatternTable` usano il parametro `masked`:

* `masked=True` → considerano solo i pattern con `Mask == True`
* `masked=False` → considerano tutti i pattern, indipendentemente dalla `Mask`

Nell’esempio seguente assumiamo:

```python
from motionpattern.pattern_table import ImportData

table = ImportData(
    path=DATA_DIR / "topk_riconteggio.csv",
    real_counting=True,
    TimeFilter=3,
    SpaceFilter=3,
)
```

### 2.1. Numero di pattern e banda

```python
# Numero di pattern totali
N_tot = table.get_N(masked=False)

# Larghezza di banda su tutti i pattern
W_tot = table.get_BandWidth(masked=False)
```

### 2.2. Entropia totale

```python
# Entropia totale di tutti i pattern
H_tot = table.get_Entropy(masked=False)

# Somma di EntropyRatio 
R_tot = table.get_EntropyRatio(masked=False)
```

### 2.3. Codifiche numeriche dei pattern selezionati

`PatternValue` è la codifica numerica del pattern (l’indice della riga).
È spesso quello che serve per salvare o passare la selezione ad altri moduli.

```python
# Codifiche numeriche di tutti i pattern
all_ids = table.get_PatternsValue(masked=False)
```

### 2.4. Pattern come array

Quando serve vedere i pattern come immagini o volumi:

* se `TimeFilter == 1` → array 2D di forma `(SpaceFilter, SpaceFilter)`
* se `TimeFilter > 1`  → array 3D di forma `(TimeFilter, SpaceFilter, SpaceFilter)`

```python
patterns_array = table.get_PatternList(masked=False)
first_pattern = patterns_array[0]
```

### 2.5. Riepilogo rapido

```python
table.print_info(masked=False)  # riepilogo su tutti i pattern
```

---

## 3. Funzioni di selezione (aggiornano `Mask`)

Sono disponibili alcune funzioni che **modificano la colonna `Mask`** per selezionare i pattern secondo criteri diversi.

```python
from motionpattern.pattern_table import (
    apply_heuristic,
    apply_rari_match_info,
    apply_comuni_match_info,
    apply_rari_match_N_W,
    apply_comuni_match_N_W,
)
```

Tutte queste funzioni:

* prendono in input una tabella `table`
* aggiornano la colonna `Mask` (sulla tabella originale o su una copia)
* permettono poi di usare i metodi visti sopra con `masked=True` per lavorare solo sui pattern scelti

### 3.1. Euristica (`apply_heuristic`)

Seleziona un sottoinsieme di pattern che rispetta:

* `Max_W` – banda massima
* `Max_N` – numero massimo di pattern

Esempio:

```python
Max_W = 0.05
Max_N = 200

table_heur = apply_heuristic(
    df=table,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,  # usa una copia della tabella
)

# Riepilogo sui pattern selezionati dall'euristica
table_heur.print_info(masked=True)

# Codifiche numeriche dei pattern selezionati
patterns_heur = table_heur.get_PatternsValue(masked=True)
```

### 3.2. Pattern rari / comuni (match sull’informazione)

Le funzioni:

* `apply_rari_match_info`
* `apply_comuni_match_info`

usano l’euristica come riferimento e costruiscono insiemi di:

* pattern più rari (probabilità piccola)
* pattern più comuni (probabilità grande)

che riproducono, il più possibile, la stessa informazione (entropia) dei pattern euristici.

Esempio schematico:

```python
table_rari, skipped_rari = apply_rari_match_info(
    df=table,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,
)

table_rari.print_info(masked=True)
ids_rari = table_rari.get_PatternsValue(masked=True)

table_comuni, skipped_comuni = apply_comuni_match_info(
    df=table,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,
)

table_comuni.print_info(masked=True)
ids_comuni = table_comuni.get_PatternsValue(masked=True)
```

### 3.3. Pattern rari / comuni (vincoli diretti su N e W)

Le funzioni:

* `apply_rari_match_N_W`
* `apply_comuni_match_N_W`

applicano direttamente i vincoli:

* somma delle probabilità `p` ≤ `Max_W`
* numero di pattern ≤ `Max_N`

selezionando rispettivamente pattern:

* più rari (`apply_rari_match_N_W`)
* più comuni (`apply_comuni_match_N_W`)

Esempio:

```python
table_rari_NW, skipped_rari_NW = apply_rari_match_N_W(
    df=table,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,
)

ids_rari_NW = table_rari_NW.get_PatternsValue(masked=True)

table_comuni_NW, skipped_comuni_NW = apply_comuni_match_N_W(
    df=table,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,
)

ids_comuni_NW = table_comuni_NW.get_PatternsValue(masked=True)
```

In tutti i casi, la logica è sempre:

1. funzione di selezione → aggiorna `Mask`
2. analisi e salvataggio → si usano i metodi con `masked=True`.

---

## 4. Dinamicità temporale: `Velocity`

Per i pattern spazio–temporali (`TimeFilter > 1`) si può misurare **quanto il pattern cambia nel tempo**.
La funzione:

```python
from motionpattern.pattern_table import add_velocity
```

aggiunge una colonna:

* `Velocity` – numero di pixel che cambiano tra un frame e il successivo, sommati su tutta la sequenza.

In pratica:

* `Velocity` alta → pattern molto dinamico
* `Velocity` bassa → pattern quasi statico nel tempo

### 4.1. Aggiungere `Velocity` alla tabella

```python
from motionpattern.pattern_table import add_velocity

add_velocity(table, inplace=True)

# Controllo veloce delle nuove colonne
table[["p", "Entropy", "Velocity"]].head()
```

### 4.2. Esempio: selezionare pattern dinamici e ottenere le loro codifiche numeriche

Combinazione tipica:

1. si importano i dati con `real_counting=True`
2. si aggiunge `Velocity`
3. si applica l’euristica
4. si impone una soglia di dinamicità
5. si estraggono le codifiche numeriche dei pattern che superano la soglia

```python
from motionpattern.pattern_table import ImportData, apply_heuristic, add_velocity

# Import dei pattern 3x3x3 con conteggio reale
table_dyn = ImportData(
    path=DATA_DIR / "topk_riconteggio.csv",
    real_counting=True,
    TimeFilter=3,
    SpaceFilter=3,
)

# Aggiungo la colonna Velocity
add_velocity(table_dyn, inplace=True)

# Applico l'euristica (vincoli su banda e numero)
Max_W = 0.05
Max_N = 200

table_heur_dyn = apply_heuristic(
    df=table_dyn,
    Max_W=Max_W,
    Max_N=Max_N,
    inplace=False,
)

# Soglia di dinamicità: tengo solo i pattern selezionati con Velocity sufficiente
velocity_threshold = 10

table_heur_dyn["Mask"] = table_heur_dyn["Mask"] & (
    table_heur_dyn["Velocity"] >= velocity_threshold
)

# Codifiche numeriche dei pattern selezionati e dinamici
dynamic_ids = table_heur_dyn.get_PatternsValue(masked=True)

print("Numero di pattern dinamici selezionati:", len(dynamic_ids))
print("Prime codifiche:", list(dynamic_ids[:10]))
```

In questo modo si ottiene direttamente la lista delle codifiche numeriche dei pattern che:

* rispettano i vincoli su banda e numero imposti dall’euristica
* hanno una dinamicità temporale almeno pari alla soglia impostata su `Velocity`.


## 5. Salvare la selezione in formato Excel

Dopo aver importato i dati, applicato l’euristica e filtrato per dinamicità, si può salvare la tabella finale in formato Excel.  
In questo esempio:

- usiamo l’euristica con `Max_W = 0.025` e `Max_N = 300`
- imponiamo `Velocity == 0` (pattern completamente statici nel tempo)
- salviamo solo i pattern selezionati (cioè `Mask == True`)

```python
from pathlib import Path
from motionpattern.pattern_table import ImportData, apply_heuristic, add_velocity

# Siamo in notebooks/, risaliamo alla root del progetto
ROOT = Path().resolve().parents[0]
DATA_DIR = ROOT / "examples" / "data"

# 1) Import dei pattern spazio–temporali 3×3×3 con conteggio reale
table = ImportData(
    path=DATA_DIR / "topk_riconteggio.csv",
    real_counting=True,
    TimeFilter=3,
    SpaceFilter=3,
)

# 2) Aggiungo la colonna Velocity
add_velocity(table, inplace=True)

# 3) Euristica
table_sel = apply_heuristic(
    df=table,
    Max_W=0.025,
    Max_N=300,
    inplace=False,
)

# 4) Dinamicità = 0 (pattern che non cambiano tra frame)
table_sel["Mask"] = table_sel["Mask"] & (table_sel["Velocity"] == 0)

# 5) Salvataggio su Excel solo delle righe selezionate
output_path = ROOT / "pattern_selezionati.xlsx"

table_sel.loc[table_sel["Mask"]].to_excel(
    output_path,
    index=True,   # mantiene PatternValue come indice
)

print("File salvato in:", output_path)

