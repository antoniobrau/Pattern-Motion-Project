import os
import cv2
import numpy as np



def binary_video_converter(
    input_path: str,
    output_path: str,
    output_width: int = None,
    output_height: int = None,
    init_frame: int = 0,
    max_frame: int = -1,
    lossless: bool = True,
    verbose: int = 1,
    adaptive_tresh: bool = False,
    dim_blocco: int = None,
    c: int = None,
) -> bool:
    """
    Converte un video in bianco e nero (binario) usando una soglia sui pixel.

    Per ogni frame:
    1. Ridimensiona il frame (se richiesto)
    2. Converte in scala di grigi
    3. Applica:
       - una soglia globale (mediana dei pixel), oppure
       - una soglia adattiva (cv2.adaptiveThreshold), se richiesto
    4. Scrive il frame binarizzato nel video di output.

    Parametri
    ---------
    input_path : str
        Percorso del file video di input.
    output_path : str
        Percorso del file video di output che verrà creato o sovrascritto.
    output_width : int, opzionale
        Larghezza del video di output. Se None, usa la larghezza originale.
    output_height : int, opzionale
        Altezza del video di output. Se None, usa l'altezza originale.
    init_frame : int, opzionale
        Numero di frame da saltare all'inizio. Default: 0.
    max_frame : int, opzionale
        Numero massimo di frame da processare. Se -1, processa tutti i frame. Default: -1.
    lossless : bool, opzionale
        Se True usa il codec FFV1 (lossless), altrimenti 'mp4v'. Default: True.
    verbose : int, opzionale
        Livello di messaggi:
        - 0: nessun messaggio
        - 1: info base
        - >1: anche progress ogni 100 frame. Default: 1.
    adaptive_tresh : bool, opzionale
        Se True usa soglia adattiva; se False usa la mediana globale. Default: False.
    dim_blocco : int, opzionale
        Dimensione del blocco per soglia adattiva (dispari, >1). Usato solo se adaptive_tresh=True.
    c : int, opzionale
        Costante sottratta alla soglia locale nella soglia adattiva. Usato solo se adaptive_tresh=True.

    Ritorno
    -------
    bool
        True se il video è stato processato con successo.
        False se viene scartato (ad es. video verticale).

    Eccezioni
    ---------
    FileNotFoundError
        Se il file di input non esiste.
    RuntimeError
        Se il video non può essere aperto.

    Esempio (uso da Python)
    ------------------------
    >>> from motionpattern.video_utils.binary_converter import binary_video_converter
    >>> binary_video_converter("input.avi", "output_binario.avi", output_width=320, output_height=240)
    True
    """

    # Verifica che il file di input esista
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Il file '{input_path}' non esiste.")
    # Apertura del video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise (f"Errore: impossibile aprire il video '{input_path}'.")

    # Ottieni proprietà del video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {input_path}")
    print(f"Risoluzione: {width}x{height}, FPS: {fps}, Frame totali: {frame_count}")

    # Verifica se l'output esiste già
    if os.path.exists(output_path):
        print(f"Attenzione: il file '{output_path}' esiste già. Verrà sovrascritto.")

    # Esclude video in orientamento verticale
    if height > width:
        print("Errore: il video ha orientamento verticale. Operazione annullata.")
        return False

    # Imposta dimensioni di output se non specificate
    if output_width is None:
        output_width = width
    if output_height is None:
        output_height = height

    # Configura il video writer per il file di output (lossless se usato FFV1)
    fourcc = cv2.VideoWriter_fourcc(*'FFV1') if lossless else cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (output_width, output_height), isColor=False)

    # Salta i frame iniziali se richiesto
    for _ in range(init_frame):
        ret, _ = cap.read()
        if not ret:
            print("Errore: raggiunto fine video durante il salto dei frame iniziali.")
            return False

    frame_index = 0  # Contatore dei frame processati

    # Inizio ciclo di lettura e processamento dei frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if max_frame >= 0 and frame_index >= max_frame:
            break

        resized_frame = frame
        # Ridimensiona il frame alle dimensioni desiderate
        resized_frame = cv2.resize(frame, (output_width, output_height))

        # Converti in scala di grigi
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

        binary_frame = gray_frame

        if adaptive_tresh:

            binary_frame = cv2.adaptiveThreshold(
                gray_frame, 255,  # Valore massimo (bianco)
                cv2.ADAPTIVE_THRESH_MEAN_C,  # Metodo: Media o Gaussiana
                cv2.THRESH_BINARY,  # Binarizzazione normale
                dim_blocco,  # Dimensione del blocco (deve essere dispari)
                c  # Costante sottratta alla soglia locale (aiuta con il contrasto)
            )
            
            # _,binary_frame = cv2.threshold(blur,median_value,255, cv2.THRESH_BINARY)
        else:
            # Calcola la mediana del frame per usarla come soglia
            median_value = np.median(gray_frame)

            # Applica la soglia binaria usando la mediana
            _, binary_frame = cv2.threshold(gray_frame, median_value, 255, cv2.THRESH_BINARY)

        #  Scrivi il frame processato nel file di output
        out.write(binary_frame )

        frame_index += 1

        # Aggiorna lo stato ogni 10 frame
        if verbose > 1 and frame_index % 100 == 0:
            print(f"Processati {frame_index}/{frame_count} frame...")

    # Rilascia le risorse
    cap.release()
    out.release()
    if verbose > 0:
        print(f"Video processato salvato in: {output_path}")
    return True