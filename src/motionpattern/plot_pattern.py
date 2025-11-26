import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def _decode_pattern_uint64(
    pattern_value: int,
    TimeFilter: int,
    SpaceFilter: int,
) -> np.ndarray:
    """
    Decodifica un pattern (intero) in un array (TimeFilter, SpaceFilter, SpaceFilter)
    seguendo la stessa convenzione di SketchGenerator.
    """
    if TimeFilter * (SpaceFilter ** 2) > 64:
        raise ValueError("TimeFilter * SpaceFilter^2 deve essere ≤ 64.")

    len_box = SpaceFilter * SpaceFilter
    n_bits = TimeFilter * len_box

    # bit LSB-first: bit_pos = 0 è il meno significativo
    bits_lsb = np.fromiter(
        ((pattern_value >> i) & 1 for i in range(n_bits)),
        dtype=np.uint8,
        count=n_bits,
    )

    # stessi shift spaziali di SketchGenerator
    spatial_shifts = np.empty((SpaceFilter, SpaceFilter), dtype=np.uint8)
    for row in range(SpaceFilter):
        for col in range(SpaceFilter):
            # bit più significativi in alto a sinistra, meno in basso a destra
            spatial_shifts[row, col] = (
                (SpaceFilter - 1 - row) * SpaceFilter
                + (SpaceFilter - 1 - col)
            )

    # shift temporali (ogni frame aggiunge len_box bit)
    temporal_shifts = np.array(
        [t * len_box for t in range(TimeFilter)],
        dtype=np.uint16,
    )

    arr = np.zeros((TimeFilter, SpaceFilter, SpaceFilter), dtype=np.uint8)
    for t in range(TimeFilter):
        base = int(temporal_shifts[t])
        for r in range(SpaceFilter):
            for c in range(SpaceFilter):
                idx = base + int(spatial_shifts[r, c])
                arr[t, r, c] = bits_lsb[idx]

    return arr


def plot_pattern(
    pattern_value: int,
    TimeFilter: int,
    SpaceFilter: int,
    show: bool = True,
    save: bool = False,
    save_dir: str | Path | None = None,
    filename: str | None = None,
) -> np.ndarray:
    """
    Visualizza (e opzionalmente salva) il pattern corrispondente a pattern_value.

    Ogni frame temporale viene mostrato in un subplot separato, affiancato,
    con un bordo nero attorno all'immagine.

    Parametri
    ---------
    pattern_value : int
        Codifica intera del pattern.
    TimeFilter : int
        Numero di frame temporali.
    SpaceFilter : int
        Lato della patch (es. 3 → 3x3).
    show : bool
        Se True mostra la figura.
    save : bool
        Se True salva la figura.
    save_dir : Path | str | None
        Cartella in cui salvare (obbligatoria se save=True).
    filename : str | None
        Nome del file da salvare (se None → 'pattern_<pattern_value>.png').

    Ritorna
    -------
    np.ndarray
        Array di shape (TimeFilter, SpaceFilter, SpaceFilter) con valori 0/1.
    """
    # decodifica in (TF, SF, SF) con la stessa convenzione dello SketchGenerator
    arr = _decode_pattern_uint64(pattern_value, TimeFilter, SpaceFilter)
    arr = arr.astype(float)  # 0/1, usati con vmin=0, vmax=1

    # figura con TF subplot affiancati
    fig, axes = plt.subplots(
        1,
        TimeFilter,
        figsize=(2 * TimeFilter, 2),
        squeeze=False,
    )
    axes = axes[0]  # shape (TimeFilter,)

    for t in range(TimeFilter):
        ax = axes[t]
        ax.imshow(arr[t], cmap="gray", vmin=0, vmax=1)
        ax.set_xticks([])
        ax.set_yticks([])

        # bordo nero attorno al frame
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("black")
            spine.set_linewidth(2)

        ax.set_title(f"t={t}")

    plt.tight_layout()

    # salvataggio opzionale
    if save:
        if save_dir is None:
            raise ValueError("save=True richiede save_dir.")
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"pattern_{pattern_value}.png"

        out_path = save_dir / filename
        fig.savefig(out_path, bbox_inches="tight", pad_inches=0)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return arr
