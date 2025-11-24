import cv2
import numpy as np
from collections import deque
from typing import List, Optional


class SketchGenerator:
    """
    Genera uno "sketch video" evidenziando solo i pattern selezionati.

    L'idea è:
    - partire da un video binario (pixel 0/1),
    - scorrere una finestra spaziale (SpaceFilter x SpaceFilter) e temporale (TimeFilter),
    - codificare ogni configurazione spaziotemporale come un intero,
    - confrontarla con un insieme di pattern di interesse,
    - ricostruire un video in cui solo i pattern selezionati vengono copiati dai frame originali.

    Parametri
    ---------
    path_in : str
        Percorso del video di input (atteso binario o almeno in scala di grigi con valori 0/255).
    path_out : str
        Percorso del video di output (sketch).
    list_patterns : list[int]
        Elenco dei pattern (interi) da mantenere nello sketch.
    TimeFilter : int
        Profondità temporale (numero di frame) usata per la finestra spaziotemporale.
    SpaceFilter : int
        Lato del filtro spaziale (es. 3 per patch 3x3).
    frame_rate : int, opzionale
        FPS del video di output. Se None, usa quello del video di input.
    max_frame : int, opzionale
        Numero massimo di frame da elaborare. Se None, usa tutti i frame disponibili.

    Attributi principali
    --------------------
    Patterns_set : set[int]
        Insieme dei pattern utilizzati per il matching.
    TimeFilter : int
        Finestra temporale.
    SpaceFilter : int
        Finestra spaziale.
    path : str
        Percorso del video di output.
    cap : cv2.VideoCapture
        Lettore del video di input.

    Esempio d'uso
    -------------
    >>> patterns = [0, 789012, 345678]
    >>> sk = SketchGenerator("examples/data/tiny_video_binary.avi", "output_sketch.avi",
    ...                      list_patterns=patterns, TimeFilter=3, SpaceFilter=3)
    >>> stats = sk.generate(lossless=True, verbose=1)
    >>> print(stats["ratio"], stats["frame_count"])
    """

    def __init__(
        self,
        path_in: str,
        path_out: str,
        list_patterns: List[int],
        TimeFilter: int,
        SpaceFilter: int,
        frame_rate: Optional[int] = None,
        max_frame: Optional[int] = None,
    ) -> None:

        self.Patterns_set: set[int] = set(list_patterns)
        self.max_frames: Optional[int] = max_frame
        self.frame_rate: Optional[int] = frame_rate

        if len(self.Patterns_set) == 0:
            raise ValueError("list_patterns è vuota: nessun pattern da usare per la ricostruzione.")

        self.TimeFilter: int = TimeFilter
        self.SpaceFilter: int = SpaceFilter
        self.len_box: int = SpaceFilter * SpaceFilter

        # Vincolo per evitare overflow nella rappresentazione dei pattern
        if self.TimeFilter * self.len_box > 64:
            raise ValueError("TimeFilter * SpaceFilter^2 deve essere ≤ 64 per evitare overflow nei pattern.")

        self.path: str = path_out
        self.cap: cv2.VideoCapture = cv2.VideoCapture(path_in)

        if not self.cap.isOpened():
            raise RuntimeError(f"Impossibile aprire il video di input: {path_in}")

        frame_height: int = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_width: int = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_length: int = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.max_frames is not None:
            self.max_frames = min(video_length, self.max_frames)
        else:
            self.max_frames = video_length

        # dimensioni griglia pattern per ogni frame
        self._patch_h = frame_height - (self.SpaceFilter - 1)
        self._patch_w = frame_width  - (self.SpaceFilter - 1)
        self.patterns_for_frame = self._patch_h * self._patch_w

        # code temporali di frame e pattern
        self.frames = deque(maxlen=self.TimeFilter)
        self.pattern_grid = deque(maxlen=self.TimeFilter)

        # tabella hash per prefiltrare i pattern
        self.dimensione_Pre_Set = 500_000
        self.Pre_Set = np.zeros(self.dimensione_Pre_Set, dtype=np.uint8)
        for _pattern in list_patterns:
            self.Pre_Set[_pattern % self.dimensione_Pre_Set] = 1

        # --- PREALLOCAZIONI PER OTTIMIZZARE ---

        # griglie temporanee riutilizzate ogni frame
        self._pattern_grid_tmp = np.zeros((self._patch_h, self._patch_w), dtype=np.uint64)
        self._box_tmp          = np.zeros((self._patch_h, self._patch_w), dtype=np.uint64)
        self._shift_tmp        = np.zeros((self._patch_h, self._patch_w), dtype=np.uint64)

        # shift spaziali precomputati (ordine bit nella patch)
        self._spatial_shifts = np.empty((self.SpaceFilter, self.SpaceFilter), dtype=np.uint8)
        for row in range(self.SpaceFilter):
            for col in range(self.SpaceFilter):
                # bit più significativi in alto a sinistra, meno in basso a destra
                self._spatial_shifts[row, col] = (
                    (self.SpaceFilter - 1 - row) * self.SpaceFilter
                    + (self.SpaceFilter - 1 - col)
                )

        # shift temporali (ogni frame aggiunge len_box bit)
        self._temporal_shifts = np.array(
            [t * self.len_box for t in range(self.TimeFilter)],
            dtype=np.uint16,
        )
    def generate(self, lossless: bool = False, verbose: int = 1) -> dict:
        """
        Genera lo sketch e salva il video di output.

        Ritorna:
            dict con chiavi:
                - ratio: pattern_accettati / pattern_totali
                - frame_count: numero di frame elaborati
                - pattern_totali: totale pattern considerati
                - pattern_accettati: totale pattern accettati
                - per_frame: lista di dict con log per frame
        """

        if len(self.Patterns_set) == 0:
            raise ValueError("Nessun pattern definito (Patterns_set è vuoto).")

        fourcc = cv2.VideoWriter_fourcc(*("FFV1" if lossless else "mp4v"))
        frame_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self.frame_rate is None:
            self.frame_rate = int(self.cap.get(cv2.CAP_PROP_FPS))

        out = cv2.VideoWriter(self.path, fourcc, self.frame_rate,
                              (frame_width, frame_height), isColor=False)

        # alias locali per velocità
        SF = self.SpaceFilter
        TF = self.TimeFilter
        ph = self._patch_h
        pw = self._patch_w
        spatial_shifts   = self._spatial_shifts
        temporal_shifts  = self._temporal_shifts
        pattern_grid_tmp = self._pattern_grid_tmp
        box_tmp          = self._box_tmp
        shift_tmp        = self._shift_tmp
        Pre_Set          = self.Pre_Set
        dim_Pre          = self.dimensione_Pre_Set
        Patterns_set     = self.Patterns_set

        # log per-frame
        per_frame_log = []

        try:
            # -------------------------
            # inizializzazione finestra temporale
            # -------------------------
            for i in range(TF):
                ret, frame = self.cap.read()
                if not ret:
                    raise ValueError(
                        f"Il video contiene solo {i} frame, ma TimeFilter={TF}."
                    )

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_frame = (frame // 255).astype(np.uint8)

                # reset griglia pattern
                pattern_grid_tmp.fill(0)

                # costruzione pattern spaziali per questo frame
                for row in range(SF):
                    for col in range(SF):
                        shift = spatial_shifts[row, col]
                        sub = gray_frame[row:row+ph, col:col+pw]
                        # shift in-place su shift_tmp, poi somma
                        np.left_shift(sub, shift, out=shift_tmp, dtype=np.uint64)
                        pattern_grid_tmp += shift_tmp

                # salviamo copia perché pattern_grid_tmp verrà riusato
                self.pattern_grid.appendleft(pattern_grid_tmp.copy())
                self.frames.appendleft(frame)

            # coda dei frame dello sketch (inizialmente grigio neutro)
            sketch_frames = deque(maxlen=TF)
            filled_frame = np.full((frame_height, frame_width), 128, dtype=np.uint8)
            for _ in range(TF):
                sketch_frames.appendleft(filled_frame.copy())

            frame_count = 0
            pattern_totali = 0
            pattern_accettati = 0

            # -------------------------
            # loop principale
            # -------------------------
            while True:
                ret, frame = self.cap.read()

                if verbose > 1 and frame_count % 10 == 0:
                    print("Frame:", frame_count)

                if not ret or (self.max_frames is not None and frame_count >= self.max_frames):
                    break

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_frame = (frame // 255).astype(np.uint8)

                # pattern spaziali per il nuovo frame
                pattern_grid_tmp.fill(0)
                for row in range(SF):
                    for col in range(SF):
                        shift = spatial_shifts[row, col]
                        sub = gray_frame[row:row+ph, col:col+pw]
                        np.left_shift(sub, shift, out=shift_tmp, dtype=np.uint64)
                        pattern_grid_tmp += shift_tmp

                # scrivi il frame più vecchio dello sketch
                out.write(sketch_frames[-1])

                # aggiorna finestre temporali
                self.pattern_grid.appendleft(pattern_grid_tmp.copy())
                self.frames.appendleft(frame)
                sketch_frames.appendleft(filled_frame.copy())

                # combiniamo i pattern temporali in box_tmp
                box_tmp.fill(0)
                for t, shift_t in enumerate(temporal_shifts):
                    np.left_shift(self.pattern_grid[t], shift_t, out=shift_tmp, dtype=np.uint64)
                    box_tmp += shift_tmp

                pattern_totali += self.patterns_for_frame

                # prefiltra con tabella hash
                mask_hash = Pre_Set[(box_tmp % dim_Pre)] != 0
                rows, cols = np.where(mask_hash)

                # log per questo frame
                accepted_this_frame = 0
                candidates_this_frame = int(len(rows))

                # controllo membership e copia patch
                for i, j in zip(rows, cols):
                    val = box_tmp[i, j]
                    if val in Patterns_set:
                        accepted_this_frame += 1
                        pattern_accettati += 1
                        for t in range(TF):
                            sketch_frames[t][i:i+SF, j:j+SF] = \
                                self.frames[t][i:i+SF, j:j+SF]

                # salva log per questo frame (prima di incrementare frame_count)
                per_frame_log.append(
                    {
                        "frame_index": frame_count,
                        "candidates_hash": candidates_this_frame,
                        "accepted": accepted_this_frame,
                    }
                )

                frame_count += 1

            # scrivi gli ultimi frame dello sketch
            for fr in reversed(sketch_frames):
                out.write(fr)

            ratio = pattern_accettati / pattern_totali if pattern_totali > 0 else 0.0

            if verbose > 0:
                print("-------------------")
                print(
                    f"Elaborazione completata, video salvato in: {self.path}.\n"
                    f"{frame_count} frame processati, banda: {ratio:.3f}."
                )

            stats = {
                "ratio": ratio,
                "frame_count": frame_count,
                "pattern_totali": int(pattern_totali),
                "pattern_accettati": int(pattern_accettati),
                "per_frame": per_frame_log,
            }

            return stats

        finally:
            self.cap.release()
            out.release()
