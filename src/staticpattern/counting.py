import numpy as np
import cv2
from pathlib import Path
import csv


def process_static_videos_to_csv(
    folder: str | Path,
    output_csv: str | Path,
    skip_frames: int = 0,
    max_frames: int | None = None,
    log_path: str | Path | None = None,
) -> dict:
    """
    Processa tutti i video nella cartella, conta i pattern statici (3×3),
    li somma, normalizza e salva un CSV compatibile con ImportData(real_counting=True).

    Parametri
    ---------
    folder : str | Path
        Cartella contenente i video.
    output_csv : str | Path
        Percorso del file CSV prodotto.
    skip_frames : int, default 0
        Numero di frame iniziali da scartare per ogni video.
    max_frames : int | None, default None
        Numero massimo di frame da processare per video (None = tutti).
    log_path : str | Path | None
        Se fornito, salva un log dettagliato (in formato TXT).

    Ritorna
    -------
    dict
        Dizionario con dati riepilogativi:
        {
            "videos_processed": n,
            "total_frames": ...,
            "total_skipped": ...,
            "occurrences_sum": array(512),
        }
    """

    folder = Path(folder)
    output_csv = Path(output_csv)

    if log_path is not None:
        log_path = Path(log_path)
        log_file = log_path.open("w", encoding="utf-8")
    else:
        log_file = None

    def log(msg: str):
        print(msg)
        if log_file is not None:
            log_file.write(msg + "\n")

    if not folder.exists():
        raise FileNotFoundError(f"Cartella non trovata: {folder}")

    occ_tot = np.zeros(512, dtype=np.int64)

    videos_processed = 0
    total_frames = 0
    total_skipped = 0

    log("=== Static Pattern Counting ===")
    log(f"Cartella: {folder}")
    log(f"Skip per video: {skip_frames} frame")
    log(f"Max frame processati per video: {max_frames}")
    log("================================\n")

    for i, video_path in enumerate(sorted(folder.glob("*.avi"))):
        log(f"[{i}] File: {video_path.name}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            log("  >> ERRORE: impossibile aprire il video. Saltato.\n")
            continue

        # scarta i frame iniziali
        skipped = 0
        for _ in range(skip_frames):
            ret, _frame = cap.read()
            if not ret:
                break
            skipped += 1

        log(f"  Frame scartati: {skipped}")
        total_skipped += skipped

        frames_processed = 0

        # conteggio frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if max_frames is not None and frames_processed >= max_frames:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            occ_tot += counting_frame(frame)

            frames_processed += 1

        cap.release()

        log(f"  Frame processati: {frames_processed}\n")

        total_frames += frames_processed
        videos_processed += 1

    # normalizzazione
    total_occ = occ_tot.sum()
    if total_occ == 0:
        raise ValueError("Errore: nessun pattern contato.")

    p = occ_tot / total_occ

    # salva CSV
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Pattern", "p"])
        for pattern_value, prob in enumerate(p):
            writer.writerow([pattern_value, prob])

    log("\n=== OUTPUT GENERATO ===")
    log(f"File CSV: {output_csv}")
    log(f"Video processati: {videos_processed}")
    log(f"Frame totali processati: {total_frames}")
    log(f"Frame totali scartati: {total_skipped}")
    log("========================")

    if log_file is not None:
        log_file.close()

    return {
        "videos_processed": videos_processed,
        "total_frames": total_frames,
        "total_skipped": total_skipped,
        "occurrences_sum": occ_tot,
    }

def counting_frame(frame: np.ndarray) -> np.ndarray:
    """
    Conta tutte le occorrenze dei pattern statici 3×3 in un frame binarizzato (0/255).

    Parametri
    ---------
    frame : np.ndarray
        Immagine 2D, valori 0 o 255.

    Ritorno
    -------
    occorrenze : np.ndarray shape (512,)
        Vettore dove occorrenze[k] = numero di patch 3×3 con valore codificato = k.

    Note
    ----
    La codifica è:
        pattern = Σ pixel * 2^posizione
    con posizione:
        ((2 - row) * 3) + (2 - col)
    cioè bit più significativi in alto a sinistra.
    """

    dim_filter = 3
    max_val = 2 ** (dim_filter * dim_filter)  # 512
    occorrenze = np.zeros(max_val, dtype=np.int64)

    # Assicura frame binario 0/1
    frame01 = (frame // 255).astype(np.uint8)

    H, W = frame01.shape
    ph = H - (dim_filter - 1)
    pw = W - (dim_filter - 1)

    # matrice temporanea per i pattern
    pattern_grid = np.zeros((ph, pw), dtype=np.uint16)

    # alias locali per velocità
    f = frame01

    # Codifica spaziale 3×3 → intero
    for row in range(dim_filter):
        for col in range(dim_filter):
            shift = (2 - row) * 3 + (2 - col)
            sub = f[row:row + ph, col:col + pw]
            pattern_grid += np.left_shift(sub, shift, dtype=np.uint16)

    # Conta le occorrenze
    np.add.at(occorrenze, pattern_grid, 1)

    return occorrenze


