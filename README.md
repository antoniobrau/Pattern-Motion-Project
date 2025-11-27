# MotionPattern Project

Questa repository raccoglie gli strumenti per analizzare e gestire pattern spaziotemporali.  

---

## Struttura della repository

### `src/motionpattern/` — Moduli principali
Contiene il codice della libreria:

- **pattern_table.py** — import dei CSV dei pattern, costruzione della tabella e funzioni di selezione  
- **binary_converter.py** — conversione dei video in binario  
- **sketch_generator.py** — generazione degli sketch a partire dai pattern selezionati  
- **spezzetta_sketch.py** — creazione delle clip digitalized + sketch  
- **pattern_encoding.py** — utilità per codifica/decodifica  

Questi moduli vengono importati direttamente negli esempi presenti nei tutorial.

---

## `notebooks/` — Ambiente di test
I notebook servono come ambiente eseguibile per provare i blocchi di codice.

---

## `examples/data/` — Dati forniti
Questa cartella contiene materiale pronto per l’uso:

- due video di esempio (normale + binarizzato)  
- livelli ottenuti con **Floating Top-k** usati nelle analisi (topk.csv)
- riconteggi reali dei pattern spaziotemporali  (topk_riconteggio.csv)
- conteggio pattern dalle immagini statiche (Del Viva)  (pattern_statici_DelViva.csv)
- pattern statici estratti dai video  (frequenze_statici_video.csv)

Permettono di eseguire la pipeline completa senza preparare altre sorgenti.

---

## `scripts/` — Strumenti da terminale
Contiene script eseguibili, come:

- `binary_video_converter.py` per la binarizzazione via CLI

---

## `output/`
Cartella opzionale per salvare sketch, clip spezzettate e risultati intermedi.

---

## Documentazione operativa (tutorial)
Le istruzioni complete, con esempi pronti, si trovano nei seguenti file:

- **MANIPOLAZIONE_DATI.md** — import, tabella dei pattern, selezione  
- **BINARY_VIDEO_CONVERTER.md** — binarizzazione dei video  
- **SKETCH_GENERATOR.md** — generazione dello sketch  
- **SPEZZETTA_SKETCH.md** — creazione delle clip spezzettate  

Ogni tutorial indica quali path modificare e come eseguire i vari moduli.

---

## Come usare la repository

1. Clonare la repository.  
2. Installare l’ambiente.  
3. Aprire i notebook.  
4. Copiare dai tutorial i blocchi relativi alla fase desiderata.  
5. Adattare i path indicati.  

---

## Installazione

Le istruzioni complete per creare l’ambiente, installare la libreria e aprire i notebook sono descritte nel **tutorial di installazione**:

👉 **INSTALLATION_TUTORIAL.md**

