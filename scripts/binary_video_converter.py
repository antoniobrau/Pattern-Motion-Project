#!/usr/bin/env python

import argparse
from pathlib import Path

from motionpattern.binary_converter import binary_video_converter


def main():
    parser = argparse.ArgumentParser(
        description="Converte un video in versione binaria (bianco/nero) frame per frame."
    )

    parser.add_argument("--input", "-i", required=True, help="Percorso del video di input.")
    parser.add_argument("--output", "-o", required=True, help="Percorso del video di output binario.")
    parser.add_argument("--width", "-W", type=int, default=None, help="Larghezza video di output.")
    parser.add_argument("--height", "-H", type=int, default=None, help="Altezza video di output.")
    parser.add_argument("--init-frame", type=int, default=0, help="Numero di frame da saltare all'inizio.")
    parser.add_argument("--max-frame", type=int, default=-1, help="Numero massimo di frame da processare.")
    parser.add_argument("--lossy", action="store_true", help="Usa codec lossy (mp4v) invece di FFV1.")
    parser.add_argument("--adaptive", action="store_true", help="Usa soglia adattiva invece della mediana globale.")
    parser.add_argument("--block", type=int, default=None, help="Dim. blocco (dispari) per soglia adattiva.")
    parser.add_argument("--c", type=int, default=None, help="Costante per soglia adattiva.")
    parser.add_argument("--verbose", type=int, default=1, help="Livello di messaggi (0,1,2,...).")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ok = binary_video_converter(
        input_path=str(input_path),
        output_path=str(output_path),
        output_width=args.width,
        output_height=args.height,
        init_frame=args.init_frame,
        max_frame=args.max_frame,
        lossless=not args.lossy,
        verbose=args.verbose,
        adaptive_tresh=args.adaptive,
        dim_blocco=args.block,
        c=args.c,
    )

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
