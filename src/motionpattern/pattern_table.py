from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import ast


class PatternTable(pd.DataFrame):
    """
    Tabella dei pattern con:
    - colonne statistiche (p, Entropy, EntropyRatio, ecc.)
    - colonna 'Mask' per selezionare un sottoinsieme di pattern
    - metodi per metriche sia sui selezionati sia sull'intera tabella.

    Formato atteso delle colonne:

        "Pattern"       --> stringa tipo "[1,0,..,1,0]" (opzionale, per ricostruzione patch)
        "p"             --> probabilità stimata
        "SpaceFilter"   --> dimensione filtro spaziale
        "TimeFilter"    --> dimensione filtro temporale
        "Entropy"       --> -p * log(p)
        "EntropyRatio"  --> Entropy / somma(Entropy)
        "PatternValue"  --> rappresentazione intera del pattern (usata come index)
        "Mask"          --> booleana (True = selezionato)

    L'indice del DataFrame è "PatternValue".
    """

    def __init__(self, data):
        if isinstance(data, PatternTable):
            data = data.copy(deep=True)
        super().__init__(data)

    # --- helper interni ---

    def _mask_or_all(self, masked: bool):
        """Restituisce una vista mascherata o l'intera tabella."""
        if masked and "Mask" in self.columns:
            return self.loc[self["Mask"]]
        return self

    # --- metriche ---

    def get_N(self, masked: bool = True) -> int:
        """
        Numero di pattern.

        masked=True  -> solo pattern con Mask == True  
        masked=False -> tutti i pattern
        """
        if masked and "Mask" in self.columns:
            return int(self["Mask"].sum())
        return int(len(self))

    def get_BandWidth(self, masked: bool = True) -> float:
        """Somma delle probabilità p (su selezionati o su tutta la tabella)."""
        df = self._mask_or_all(masked)
        return float(df["p"].sum())

    def get_Entropy(self, masked: bool = True) -> float:
        """Entropia totale (somma di 'Entropy')."""
        df = self._mask_or_all(masked)
        return float(df["Entropy"].sum())

    def get_EntropyRatio(self, masked: bool = True) -> float:
        """Somma di 'EntropyRatio'."""
        df = self._mask_or_all(masked)
        return float(df["EntropyRatio"].sum())

    def get_PatternsValue(self, masked: bool = True) -> pd.Index:
        """
        Restituisce i PatternValue (indice).

        masked=True  -> solo pattern selezionati  
        masked=False -> tutti i pattern
        """
        if masked and "Mask" in self.columns:
            return self.index[self["Mask"]]
        return self.index

    def get_PatternList(self, masked: bool = True):
        """
        Restituisce una lista di pattern come array.

        - Se TimeFilter == 1  -> ogni pattern è un array 2D  (SpaceFilter, SpaceFilter)
        - Se TimeFilter > 1   -> ogni pattern è un array 3D  (TimeFilter, SpaceFilter, SpaceFilter)

        La colonna 'Pattern' può essere:
        - una stringa tipo "[0,1,...]" (pattern esplicito)
        - un intero che codifica il pattern in binario (PatternValue)

        In entrambi i casi i valori finali sono uint8 in {0, 255}.
        """
        df = self._mask_or_all(masked)

        if "Pattern" not in df.columns:
            raise ValueError("get_PatternList richiede la colonna 'Pattern'.")

        if df.empty:
            return []

        time_filter = int(self["TimeFilter"].iloc[0])
        space_filter = int(self["SpaceFilter"].iloc[0])
        n_bits = time_filter * space_filter * space_filter

        lista = []

        first = df["Pattern"].iloc[0]

        # Caso 1: Pattern è una stringa tipo "[0,1,...]"
        if isinstance(first, str) and first.strip().startswith("["):
            if time_filter == 1:
                # pattern statici: array 2D (SpaceFilter, SpaceFilter)
                for s in df["Pattern"]:
                    arr = np.array(ast.literal_eval(s), dtype=np.uint8)
                    arr = arr.reshape((space_filter, space_filter))
                    lista.append(255 * arr)
            else:
                # pattern spaziotemporali: array 3D (TimeFilter, SpaceFilter, SpaceFilter)
                for s in df["Pattern"]:
                    arr = np.array(ast.literal_eval(s), dtype=np.uint8)
                    arr = arr.reshape((time_filter, space_filter, space_filter))
                    lista.append(255 * arr)

            return lista

        # Caso 2: Pattern è numerico (codifica binaria)
        # Converto ogni valore in stringa binaria a n_bits, poi reshaping
        for v in df["Pattern"]:
            v_int = int(v)
            bits = format(v_int, f"0{n_bits}b")  # stringa tipo "010101..."
            arr = np.fromiter((1 if b == "1" else 0 for b in bits), dtype=np.uint8)

            if time_filter == 1:
                arr = arr.reshape((space_filter, space_filter))
            else:
                arr = arr.reshape((time_filter, space_filter, space_filter))

            lista.append(255 * arr)

        return lista


    def print_info(self, masked: bool = True) -> None:
        """
        Stampa un riepilogo delle metriche.

        masked=True  -> solo pattern selezionati  
        masked=False -> tutta la tabella
        """
        scope = "selezionati" if masked else "totali"
        print(f"Numero di pattern {scope}: {self.get_N(masked)}")
        print(f"Larghezza di banda (somma p): {self.get_BandWidth(masked):.6f}")
        print(f"Entropia totale: {self.get_Entropy(masked):.6f}")
        print(f"Somma EntropyRatio: {self.get_EntropyRatio(masked):.6f}")

def ImportData(
    path: Path | str,
    real_counting: bool = False,
    p: float = 0.999,
    TimeFilter: int | None = None,
    SpaceFilter: int | None = None,
) -> PatternTable:
    """
    Importa un file di pattern e restituisce un PatternTable.

    Parametri
    ---------
    path : str | Path
        Percorso del file da importare.
        - Se real_counting=False: file di output del Floating Top-k (con header commentato).
        - Se real_counting=True: CSV con probabilità già stimate (colonna 'p').
    real_counting : bool, default False
        Se False: interpreta il file come output dell'algoritmo (Sum_level, Count_level, ecc.).
        Se True: interpreta il file come file di probabilità reali dei pattern.
    p : float, default 0.999
        Parametro usato nella formula di stima di p nel caso real_counting=False.
    TimeFilter : int | None
        Filtro temporale (numero di frame nella finestra spaziotemporale).
        - Se real_counting=False: se None viene letto dall'header del file;
          se non None viene controllata la consistenza con il valore nell'header.
        - Se real_counting=True: deve essere fornito (non può essere None).
    SpaceFilter : int | None
        Filtro spaziale (lato della patch).
        - Se real_counting=False: se None viene letto dall'header del file;
          se non None viene controllata la consistenza con il valore nell'header.
        - Se real_counting=True: deve essere fornito (non può essere None).

    Ritorno
    -------
    PatternTable
        DataFrame indicizzato per PatternValue, con colonne:
        ['Pattern', 'p', 'SpaceFilter', 'Entropy', 'EntropyRatio',
         'TimeFilter', 'PatternValue', 'Mask', 'TotalIterations' (se disponibile)]
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")

    if not real_counting:
        # File Floating Top-k: header con metadati nelle prime righe commentate
        with path.open("r") as f:
            f.readline()             # scarta prima riga
            line = f.readline()[1:]  # togli prefisso commento (es. '#')
            line = line.strip()
            lista = line.split(";")[:-1]

        TotalIterations_h, SpaceFilter_h, TimeFilter_h, PoolSize, DimMultiLevel = map(float, lista)

        # TimeFilter / SpaceFilter: se passati, controlla consistenza
        if TimeFilter is None:
            TimeFilter_val = int(TimeFilter_h)
        else:
            if int(TimeFilter_h) != int(TimeFilter):
                raise ValueError(
                    f"Incoerenza TimeFilter: header={int(TimeFilter_h)}, argomento={int(TimeFilter)}"
                )
            TimeFilter_val = int(TimeFilter)

        if SpaceFilter is None:
            SpaceFilter_val = int(SpaceFilter_h)
        else:
            if int(SpaceFilter_h) != int(SpaceFilter):
                raise ValueError(
                    f"Incoerenza SpaceFilter: header={int(SpaceFilter_h)}, argomento={int(SpaceFilter)}"
                )
            SpaceFilter_val = int(SpaceFilter)

        data = pd.read_csv(path, sep=";", comment="#")

        # stima di p secondo la formula usata
        data["p"] = (
            PoolSize
            * np.exp(data["Sum_level"] / data["Count_level"] * (1 - p) - np.euler_gamma)
            / TotalIterations_h
        )

        data["Entropy"] = -data["p"] * np.log(data["p"].where(data["p"] > 0, np.nan))
        data["Entropy"] = data["Entropy"].fillna(0.0)

        total_entropy = data["Entropy"].sum()
        if total_entropy > 0:
            data["EntropyRatio"] = data["Entropy"] / total_entropy
        else:
            data["EntropyRatio"] = 0.0

        data["TotalIterations"] = TotalIterations_h
        data["Mask"] = True
        data["PatternValue"] = data["Pattern"]
        data["SpaceFilter"] = SpaceFilter_val
        data["TimeFilter"] = TimeFilter_val

        columns = [
            "Pattern",
            "p",
            "SpaceFilter",
            "Entropy",
            "EntropyRatio",
            "TimeFilter",
            "PatternValue",
            "Mask",
            "TotalIterations",
        ]
        data = data[columns]
        data.set_index("PatternValue", inplace=True)

        return PatternTable(data)

    # real_counting = True: file con probabilità già stimate (colonna 'p')
    data = pd.read_csv(path, sep=";", comment="#")

    if "p" not in data.columns:
        raise ValueError("Per real_counting=True il file deve avere una colonna 'p'.")

    # TimeFilter / SpaceFilter in questo caso devono essere passati esplicitamente
    if TimeFilter is None or SpaceFilter is None:
        raise ValueError(
            "Per real_counting=True è necessario specificare TimeFilter e SpaceFilter."
        )

    TimeFilter_val = int(TimeFilter)
    SpaceFilter_val = int(SpaceFilter)

    # PatternValue = Pattern se presente, altrimenti usa index numerico
    if "Pattern" in data.columns:
        data["PatternValue"] = data["Pattern"]
    else:
        data["PatternValue"] = np.arange(len(data), dtype=np.int64)

    # Controllo di base sui valori di p
    if (data["p"] < 0).any():
        raise ValueError("La colonna 'p' contiene valori negativi.")
    total_p = data["p"].sum()
    if total_p <= 0:
        raise ValueError("La somma dei valori di 'p' è nulla o negativa.")

    # Entropia e rapporto di entropia
    data["Entropy"] = -data["p"] * np.log(data["p"].where(data["p"] > 0, np.nan))
    data["Entropy"] = data["Entropy"].fillna(0.0)

    total_entropy = data["Entropy"].sum()
    if total_entropy > 0:
        data["EntropyRatio"] = data["Entropy"] / total_entropy
    else:
        data["EntropyRatio"] = 0.0

    data["Mask"] = True  # tutti selezionati inizialmente
    data["TimeFilter"] = TimeFilter_val
    data["SpaceFilter"] = SpaceFilter_val

    columns_base = [
        "Pattern",
        "p",
        "Entropy",
        "EntropyRatio",
        "PatternValue",
        "Mask",
        "TimeFilter",
        "SpaceFilter",
    ]
    columns = [c for c in columns_base if c in data.columns]
    data = data[columns]
    data.set_index("PatternValue", inplace=True)

    return PatternTable(data)

def apply_heuristic(
    df: PatternTable,
    Max_W: float,
    Max_N: int,
    inplace: bool = True,
) -> PatternTable:
    """
    Applica l'euristica di selezione dei pattern aggiornando la colonna 'Mask'.

    Euristica:
        Euristica = Entropy / max(1/Max_N, p/Max_W)

    I pattern vengono ordinati per 'Euristica' decrescente e se ne
    seleziona il massimo numero tale che:
        - il numero di pattern <= Max_N
        - la somma delle p dei selezionati <= Max_W

    Parametri
    ---------
    df : PatternTable
        Tabella dei pattern su cui applicare l'euristica.
    Max_W : float
        Massima larghezza di banda totale (somma p) dei pattern selezionati.
    Max_N : int
        Numero massimo di pattern selezionati.
    inplace : bool, default True
        Se True modifica df in place e lo restituisce.
        Se False lavora su una copia e restituisce la copia.

    Ritorno
    -------
    PatternTable
        Tabella con colonne 'Euristica' e 'Mask' aggiornate.
    """
    if not inplace:
        df = PatternTable(df)  # copia

    # euristica
    df["Euristica"] = df["Entropy"] / np.maximum(
        np.ones(df["p"].shape) / Max_N,
        df["p"] / Max_W,
    )

    # ordino per euristica decrescente
    data_temp = df.sort_values(by="Euristica", ascending=False)

    # cerco quanti pattern posso prendere rispettando Max_W
    elements = Max_N
    while elements > 0 and data_temp["p"].iloc[:elements].sum() > Max_W:
        elements -= 1

    selected_indices = data_temp.index[:elements]
    df["Mask"] = df.index.isin(selected_indices)

    return df


def apply_rari_match_info(
    df: PatternTable,
    Max_W: float,
    Max_N: int,
    inplace: bool = True,
) -> tuple[PatternTable, int]:
    """
    Selezione di pattern rari (p piccola) che replica l'informazione (Entropia totale)
    dei pattern scelti dall'euristica con gli stessi vincoli N, W.

    Passi:
    1) Si applica l'euristica standard con (Max_W, Max_N) su una copia di df.
       La somma di 'Entropy' sui pattern selezionati definisce info_target.
    2) Si ordina l'intera tabella per 'p' crescente (pattern più rari per primi).
    3) Si contano e si saltano i pattern iniziali per cui l'entropia singola
       supera info_target (non possono far parte di una selezione che stia
       sotto info_target).
    4) A partire dal primo pattern che non supera info_target, si accumulano
       pattern in ordine di rarità finché la somma di 'Entropy' non supererebbe
       info_target.
    5) Si aggiorna la colonna 'Mask' con la nuova selezione.

    Parametri
    ---------
    df : PatternTable
        Tabella dei pattern.
    Max_W : float
        Larghezza di banda usata dall'euristica per definire info_target.
    Max_N : int
        Numero massimo di pattern usato dall'euristica per definire info_target.
    inplace : bool, default True
        Se True modifica df in place; se False lavora su una copia.

    Ritorno
    -------
    (PatternTable, int)
        - il PatternTable con 'Mask' aggiornata
        - il numero di pattern scartati prima di iniziare l'accumulo
    """
    if not inplace:
        df = PatternTable(df)

    # baseline: selezione euristica per definire info_target
    df_heur = apply_heuristic(df, Max_W=Max_W, Max_N=Max_N, inplace=False)
    info_target = float(df_heur.loc[df_heur["Mask"], "Entropy"].sum())

    if info_target <= 0:
        df["Mask"] = False
        return df, 0

    # ordina per p crescente (pattern rari per primi)
    data_temp = df.sort_values(by="p", ascending=True)

    # trova il primo pattern con Entropy <= info_target
    start_idx = None
    for i, (_, row) in enumerate(data_temp.iterrows()):
        if row["Entropy"] <= info_target:
            start_idx = i
            break

    skipped_before = 0 if start_idx is None else start_idx

    if start_idx is None:
        # nessun pattern singolo ha entropia compatibile con info_target
        df["Mask"] = False
        return df, skipped_before

    selected = []
    sum_info = 0.0

    # accumula pattern rari finché non superi info_target
    for _, row in data_temp.iloc[start_idx:].iterrows():
        e = float(row["Entropy"])
        if sum_info + e > info_target:
            break
        selected.append(row.name)
        sum_info += e

    df["Mask"] = df.index.isin(selected)
    return df, skipped_before


def apply_comuni_match_info(
    df: PatternTable,
    Max_W: float,
    Max_N: int,
    inplace: bool = True,
) -> tuple[PatternTable, int]:
    """
    Selezione di pattern comuni (p grande) che replica l'informazione (Entropia totale)
    dei pattern scelti dall'euristica con gli stessi vincoli N, W.

    Passi:
    1) Si applica l'euristica standard con (Max_W, Max_N) su una copia di df.
       La somma di 'Entropy' sui pattern selezionati definisce info_target.
    2) Si ordina l'intera tabella per 'p' decrescente (pattern più comuni per primi).
    3) Si contano e si saltano i pattern iniziali la cui entropia singola
       supera info_target.
    4) A partire dal primo pattern che non supera info_target, si accumulano
       pattern in ordine di comunanza finché la somma di 'Entropy' non supererebbe
       info_target.
    5) Si aggiorna la colonna 'Mask' con la nuova selezione.

    Parametri
    ---------
    df : PatternTable
        Tabella dei pattern.
    Max_W : float
        Larghezza di banda usata dall'euristica per definire info_target.
    Max_N : int
        Numero massimo di pattern usato dall'euristica per definire info_target.
    inplace : bool, default True
        Se True modifica df in place; se False lavora su una copia.

    Ritorno
    -------
    (PatternTable, int)
        - il PatternTable con 'Mask' aggiornata
        - il numero di pattern scartati prima di iniziare l'accumulo
    """
    if not inplace:
        df = PatternTable(df)

    # baseline: selezione euristica per definire info_target
    df_heur = apply_heuristic(df, Max_W=Max_W, Max_N=Max_N, inplace=False)
    info_target = float(df_heur.loc[df_heur["Mask"], "Entropy"].sum())

    if info_target <= 0:
        df["Mask"] = False
        return df, 0

    # ordina per p decrescente (pattern comuni per primi)
    data_temp = df.sort_values(by="p", ascending=False)

    # trova il primo pattern con Entropy <= info_target
    start_idx = None
    for i, (_, row) in enumerate(data_temp.iterrows()):
        if row["Entropy"] <= info_target:
            start_idx = i
            break

    skipped_before = 0 if start_idx is None else start_idx

    if start_idx is None:
        df["Mask"] = False
        return df, skipped_before

    selected = []
    sum_info = 0.0

    # accumula pattern comuni finché non superi info_target
    for _, row in data_temp.iloc[start_idx:].iterrows():
        e = float(row["Entropy"])
        if sum_info + e > info_target:
            break
        selected.append(row.name)
        sum_info += e

    df["Mask"] = df.index.isin(selected)
    return df, skipped_before


def apply_rari_match_N_W(
    df: PatternTable,
    Max_W: float,
    Max_N: int,
    inplace: bool = True,
) -> tuple[PatternTable, int]:
    """
    Selezione di pattern rari (p piccola) imponendo direttamente i vincoli:
        - somma delle probabilità p <= Max_W
        - numero di pattern selezionati <= Max_N

    Passi:
    1) Si ordina la tabella per 'p' crescente.
    2) Si contano e si saltano i pattern iniziali per cui la probabilità singola
       supera Max_W (non possono mai soddisfare il vincolo di banda).
    3) A partire dal primo pattern per cui p <= Max_W, si accumulano pattern
       in ordine di rarità finché:
           - il numero di pattern rimane <= Max_N
           - la somma delle p non supererebbe Max_W.
       Non si aggiunge l'ultimo pattern che violerebbe uno dei vincoli.
    4) Si aggiorna la colonna 'Mask' con la nuova selezione.

    Parametri
    ---------
    df : PatternTable
        Tabella dei pattern.
    Max_W : float
        Banda massima (somma p) consentita.
    Max_N : int
        Numero massimo di pattern consentito.
    inplace : bool, default True
        Se True modifica df in place; se False lavora su una copia.

    Ritorno
    -------
    (PatternTable, int)
        - il PatternTable con 'Mask' aggiornata
        - il numero di pattern scartati prima di iniziare l'accumulo
    """
    if not inplace:
        df = PatternTable(df)

    data_temp = df.sort_values(by="p", ascending=True)

    # trova il primo pattern con p <= Max_W
    start_idx = None
    for i, (_, row) in enumerate(data_temp.iterrows()):
        if float(row["p"]) <= Max_W:
            start_idx = i
            break

    skipped_before = 0 if start_idx is None else start_idx

    if start_idx is None:
        df["Mask"] = False
        return df, skipped_before

    selected = []
    sum_p = 0.0
    count = 0

    for _, row in data_temp.iloc[start_idx:].iterrows():
        p_i = float(row["p"])

        # controllo dei vincoli sul candidato successivo
        if count + 1 > Max_N or sum_p + p_i > Max_W:
            break

        selected.append(row.name)
        sum_p += p_i
        count += 1

    df["Mask"] = df.index.isin(selected)
    return df, skipped_before


def apply_comuni_match_N_W(
    df: PatternTable,
    Max_W: float,
    Max_N: int,
    inplace: bool = True,
) -> tuple[PatternTable, int]:
    """
    Selezione di pattern comuni (p grande) imponendo direttamente i vincoli:
        - somma delle probabilità p <= Max_W
        - numero di pattern selezionati <= Max_N

    Passi:
    1) Si ordina la tabella per 'p' decrescente.
    2) Si contano e si saltano i pattern iniziali per cui la probabilità singola
       supera Max_W.
    3) A partire dal primo pattern per cui p <= Max_W, si accumulano pattern
       in ordine di comunanza finché:
           - il numero di pattern rimane <= Max_N
           - la somma delle p non supererebbe Max_W.
       Non si aggiunge l'ultimo pattern che violerebbe uno dei vincoli.
    4) Si aggiorna la colonna 'Mask' con la nuova selezione.

    Parametri
    ---------
    df : PatternTable
        Tabella dei pattern.
    Max_W : float
        Banda massima (somma p) consentita.
    Max_N : int
        Numero massimo di pattern consentito.
    inplace : bool, default True
        Se True modifica df in place; se False lavora su una copia.

    Ritorno
    -------
    (PatternTable, int)
        - il PatternTable con 'Mask' aggiornata
        - il numero di pattern scartati prima di iniziare l'accumulo
    """
    if not inplace:
        df = PatternTable(df)

    data_temp = df.sort_values(by="p", ascending=False)

    # trova il primo pattern con p <= Max_W
    start_idx = None
    for i, (_, row) in enumerate(data_temp.iterrows()):
        if float(row["p"]) <= Max_W:
            start_idx = i
            break

    skipped_before = 0 if start_idx is None else start_idx

    if start_idx is None:
        df["Mask"] = False
        return df, skipped_before

    selected = []
    sum_p = 0.0
    count = 0

    for _, row in data_temp.iloc[start_idx:].iterrows():
        p_i = float(row["p"])

        if count + 1 > Max_N or sum_p + p_i > Max_W:
            break

        selected.append(row.name)
        sum_p += p_i
        count += 1

    df["Mask"] = df.index.isin(selected)
    return df, skipped_before






import numpy as np
import pandas as pd

# ... sopra hai già PatternTable, ImportData, ecc. ...


def add_velocity(table, inplace: bool = True):
    """
    Aggiunge una colonna 'Velocity' al PatternTable.

    Velocity è definita solo se:
      - TimeFilter > 1
      - esiste la colonna 'Pattern' con pattern codificati come interi.

    Per ogni pattern:
      - lo decodifica in un array (TimeFilter, SpaceFilter, SpaceFilter) di 0/1
      - conta quanti pixel cambiano da un frame al successivo (somma su tutti i tempi)
    """

    if not inplace:
        table = table.copy()

    if "TimeFilter" not in table.columns or "SpaceFilter" not in table.columns:
        raise ValueError("add_velocity richiede le colonne 'TimeFilter' e 'SpaceFilter'.")

    if "Pattern" not in table.columns:
        raise ValueError("add_velocity richiede la colonna 'Pattern' (interi codificati).")

    # Controllo che TimeFilter e SpaceFilter siano costanti
    TF = int(table["TimeFilter"].iloc[0])
    SF = int(table["SpaceFilter"].iloc[0])

    if (table["TimeFilter"] != TF).any() or (table["SpaceFilter"] != SF).any():
        raise ValueError("add_velocity assume TimeFilter e SpaceFilter costanti su tutta la tabella.")

    if TF <= 1:
        raise ValueError("Velocity è definita solo per TimeFilter > 1.")

    n_bits = TF * (SF * SF)

    def _pattern_int_to_array(n: int) -> np.ndarray:
        """Decodifica l'intero n in array (TF, SF, SF) di 0/1."""
        # stringa binaria lunga n_bits con padding a sinistra
        b = format(int(n), f"0{n_bits}b")
        arr = np.fromiter((1 if ch == "1" else 0 for ch in b), dtype=np.uint8, count=n_bits)
        return arr.reshape((TF, SF, SF))

    def _temporal_change_speed_from_int(n: int) -> int:
        """
        Conta quanti pixel cambiano tra frame consecutivi.
        """
        a = _pattern_int_to_array(n)  # shape (TF, SF, SF), valori 0/1
        # differenza temporale: a[t] vs a[t+1]
        diff = a[1:] != a[:-1]        # shape (TF-1, SF, SF), bool
        return int(np.sum(diff))

    # calcola velocity riga per riga
    velocity = table["Pattern"].apply(_temporal_change_speed_from_int)

    table["Velocity"] = velocity

    return table




def is_static(pattern_value: int, TimeFilter: int, SpaceFilter: int) -> bool:
    """
    Ritorna True se il pattern (codificato come intero) è statico,
    cioè se tutti i frame temporali sono identici.

    TimeFilter deve essere > 1.
    """

    if TimeFilter <= 1:
        raise ValueError("is_static richiede TimeFilter > 1.")

    n_bits = TimeFilter * (SpaceFilter * SpaceFilter)

    # decodifica coerente con add_velocity
    b = format(int(pattern_value), f"0{n_bits}b")
    arr = np.fromiter((1 if ch == "1" else 0 for ch in b),
                      dtype=np.uint8,
                      count=n_bits).reshape((TimeFilter, SpaceFilter, SpaceFilter))

    # confronto frame per frame
    return np.all(arr[1:] == arr[0])