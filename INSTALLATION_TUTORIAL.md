

# 📘 MotionPattern – Tutorial di Installazione

Questa guida descrive come installare e aggiornare il progetto **MotionPattern** su **Windows**, **macOS** e **Linux**, utilizzando un ambiente Python isolato all’interno della cartella del progetto.

---

# 🧰 Requisiti

* Python **3.10 o 3.11**
* Git installato sul sistema
* Terminale del sistema operativo (CMD, Terminal, Bash)

---

# 🟦 Installazione su Windows

### 1. Aprire CMD

### 2. Clonare la repository

```cmd
git clone https://github.com/TUO_USERNAME/Pattern-Motion-Project.git
cd Pattern-Motion-Project
```

### 3. Creare l’ambiente virtuale

```cmd
python -m venv .venv
```

### 4. Attivarlo

```cmd
.\.venv\Scripts\activate.bat
```

### 5. Installare il progetto

```cmd
pip install --upgrade pip
pip install -e .
```

### 6. Installare Jupyter e il kernel

```cmd
pip install jupyterlab ipykernel notebook
python -m ipykernel install --user --name motionpattern --display-name "MotionPattern"
```

### 7. Avviare Jupyter Lab

```cmd
jupyter lab
```

Selezionare il kernel **MotionPattern** nei notebook.

---

# 🟩 Installazione su macOS

### 1. Aprire il Terminale

### 2. Clonare la repository

```bash
git clone https://github.com/TUO_USERNAME/Pattern-Motion-Project.git
cd Pattern-Motion-Project
```

### 3. Creare l’ambiente virtuale

```bash
python3 -m venv .venv
```

### 4. Attivarlo

```bash
source .venv/bin/activate
```

### 5. Installare il progetto

```bash
pip install --upgrade pip
pip install -e .
```

### 6. Installare Jupyter e il kernel

```bash
pip install jupyterlab ipykernel notebook
python3 -m ipykernel install --user --name motionpattern --display-name "MotionPattern"
```

### 7. Avviare Jupyter Lab

```bash
jupyter lab
```

---

# 🟥 Installazione su Linux

### 1. Aprire il Terminale

### 2. Clonare la repository

```bash
git clone https://github.com/TUO_USERNAME/Pattern-Motion-Project.git
cd Pattern-Motion-Project
```

### 3. Creare la venv

```bash
python3 -m venv .venv
```

### 4. Attivarla

```bash
source .venv/bin/activate
```

### 5. Installare il progetto

```bash
pip install --upgrade pip
pip install -e .
```

### 6. Installare Jupyter e il kernel

```bash
pip install jupyterlab ipykernel notebook
python3 -m ipykernel install --user --name motionpattern --display-name "MotionPattern"
```

### 7. Avviare Jupyter Lab

```bash
jupyter lab
```

---

# 🔄 Aggiornamento del progetto (tutti i sistemi)

### 1. Entrare nella cartella del progetto

```bash
cd PATH/TO/Pattern-Motion-Project
```

### 2. Ottenere gli aggiornamenti

```bash
git pull
```

### 3. Attivare l’ambiente

**Windows**

```cmd
.\.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 4. Reinstallare (solo se sono cambiate le dipendenze)

```bash
pip install -e .
```

### 5. Avviare Jupyter

```bash
jupyter lab
```

---

# 🗂️ Ambiente isolato

Il progetto utilizza un ambiente virtuale contenuto direttamente nella cartella:

```
Pattern-Motion-Project/
    .venv/
    src/
    notebooks/
    pyproject.toml
```

Le librerie necessarie vengono installate solo nel contenitore `.venv`, senza modificare Python di sistema o altri progetti.

### Per rimuovere tutto:

```
eliminare la cartella Pattern-Motion-Project
```

---

# 🧪 Test dell’installazione

Nel primo notebook inserire:

```python
import motionpattern
from motionpattern.pattern_table import ImportData
from motionpattern.sketch_generator import SketchGenerator

print("Installazione OK!")
```

Se non compaiono errori la configurazione è completata.

---

