import cv2
from pathlib import Path
import numpy as np


def spezzetta_sketch(
    folder_bin: Path,
    folder_sketch: Path,
    out_folder_bin: Path,
    out_folder_sketch: Path,
    bin_prefix: str,
    sketch_prefix: str,
    out_bin_prefix: str,
    out_sketch_prefix: str,
    len_sketch: int = 3,
    extra: int = 2,
    padding: int = 15,
    codec: str = "FFV1",
    seed: int | None = None,
):
    """
    Per ogni video binarizzato e relativo sketch, genera due video spezzettati:
    - Digitalized: finestra più larga (extra frame a sinistra e destra).
    - Sketch: finestra centrale di lunghezza len_sketch.

    I nomi sono del tipo:
    - binarizzato:   bin_prefix   + id + ".avi"
    - sketch input:  sketch_prefix + id + ".avi"
    - out digital:   out_bin_prefix + id + ".avi"
    - out sketch:    out_sketch_prefix + id + ".avi"
    """

    folder_bin = Path(folder_bin)
    folder_sketch = Path(folder_sketch)
    out_folder_bin = Path(out_folder_bin)
    out_folder_sketch = Path(out_folder_sketch)

    out_folder_bin.mkdir(parents=True, exist_ok=True)
    out_folder_sketch.mkdir(parents=True, exist_ok=True)

    if seed is not None:
        np.random.seed(seed)

    # Prendo tutti i binarizzati e ricavo gli id
    bin_files = sorted(folder_bin.glob(f"{bin_prefix}*.avi"))
    if not bin_files:
        raise RuntimeError(f"Nessun file binarizzato trovato in {folder_bin} con prefisso '{bin_prefix}'")

    bin_ids = set(f.stem[len(bin_prefix):] for f in bin_files)

    # Controllo che per ogni id esista lo sketch
    sketch_ids = set()
    for f in folder_sketch.glob(f"{sketch_prefix}*.avi"):
        sketch_ids.add(f.stem[len(sketch_prefix):])

    # Mismatch tra insiemi → errore
    missing_sketch = bin_ids - sketch_ids
    missing_bin = sketch_ids - bin_ids

    if missing_sketch:
        raise RuntimeError(f"Mancano gli sketch per questi id: {sorted(missing_sketch)}")
    if missing_bin:
        raise RuntimeError(f"Mancano i binarizzati per questi id: {sorted(missing_bin)}")

    # Ora processiamo ogni id
    for vid_id in sorted(bin_ids):
        bin_path = folder_bin / f"{bin_prefix}{vid_id}.avi"
        sk_path = folder_sketch / f"{sketch_prefix}{vid_id}.avi"

        cap_bin = None
        cap_sk = None
        out_bin = None
        out_sk = None

        try:
            cap_bin = cv2.VideoCapture(str(bin_path))
            cap_sk = cv2.VideoCapture(str(sk_path))

            if not cap_bin.isOpened():
                raise RuntimeError(f"Non riesco ad aprire il binarizzato: {bin_path}")
            if not cap_sk.isOpened():
                raise RuntimeError(f"Non riesco ad aprire lo sketch: {sk_path}")

            frame_width = int(cap_bin.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap_bin.get(cv2.CAP_PROP_FRAME_HEIGHT))

            frame_total_bin = int(cap_bin.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_total_sk = int(cap_sk.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_total_min = min(frame_total_bin, frame_total_sk)

            needed = len_sketch + 2 * extra
            if frame_total_min < needed:
                raise RuntimeError(
                    f"Video troppo corto per id={vid_id}: min frame={frame_total_min}, richiesti={needed}"
                )

            # Scelta t: frame iniziale dello sketch
            # t può andare da extra fino (frame_total_min - extra - len_sketch)
            low = extra
            high = frame_total_min - extra - len_sketch + 1  # esclusivo

            if high <= low:
                raise RuntimeError(
                    f"Nessuna finestra valida per id={vid_id}: low={low}, high={high}, frame_min={frame_total_min}"
                )

            t = np.random.randint(low, high)

            # Finestra:
            # sketch:       [t, t + len_sketch - 1]
            # digitalized:  [t - extra, t + len_sketch - 1 + extra]
            start_dig = t - extra
            end_dig = t + len_sketch - 1 + extra
            start_sk = t
            end_sk = t + len_sketch - 1

            # FPS
            fps = cap_bin.get(cv2.CAP_PROP_FPS)
            if fps is None or fps <= 0:
                fps = 30.0

            fourcc = cv2.VideoWriter_fourcc(*codec)

            out_bin_path = out_folder_bin / f"{out_bin_prefix}{vid_id}.avi"
            out_sk_path = out_folder_sketch / f"{out_sketch_prefix}{vid_id}.avi"

            out_bin = cv2.VideoWriter(str(out_bin_path), fourcc, fps, (frame_width, frame_height), isColor=False)
            out_sk = cv2.VideoWriter(str(out_sk_path), fourcc, fps, (frame_width, frame_height), isColor=False)

            if not out_bin.isOpened():
                raise RuntimeError(f"VideoWriter digitalized non si è aperto: {out_bin_path}")
            if not out_sk.isOpened():
                raise RuntimeError(f"VideoWriter sketch non si è aperto: {out_sk_path}")

            # Padding grigio
            gray = np.ones((frame_height, frame_width), dtype=np.uint8) * 128

            for _ in range(padding):
                out_bin.write(gray)
                out_sk.write(gray)

            frame_idx = 0
            while True:
                ret_bin, frame_bin = cap_bin.read()
                ret_sk, frame_sk = cap_sk.read()

                if not ret_bin or not ret_sk:
                    break

                frame_bin = cv2.cvtColor(frame_bin, cv2.COLOR_BGR2GRAY)
                frame_sk = cv2.cvtColor(frame_sk, cv2.COLOR_BGR2GRAY)

                assert frame_bin.ndim == 2 and frame_bin.dtype == np.uint8
                assert frame_sk.ndim == 2 and frame_sk.dtype == np.uint8

                # Digitalized: finestra larga
                if start_dig <= frame_idx <= end_dig:
                    out_bin.write(frame_bin)

                # Sketch: finestra centrale
                if start_sk <= frame_idx <= end_sk:
                    out_sk.write(frame_sk)

                # Se abbiamo superato la finestra massima, possiamo anche uscire
                if frame_idx > end_dig:
                    break

                frame_idx += 1

            for _ in range(padding):
                out_bin.write(gray)
                out_sk.write(gray)

            print(f"OK id={vid_id}, t={t}, bin={bin_path.name}, sk={sk_path.name}")

        finally:
            if out_bin is not None and out_bin.isOpened():
                out_bin.release()
            if out_sk is not None and out_sk.isOpened():
                out_sk.release()
            if cap_bin is not None and cap_bin.isOpened():
                cap_bin.release()
            if cap_sk is not None and cap_sk.isOpened():
                cap_sk.release()
