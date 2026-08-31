#!/usr/bin/env python3
"""Optimiza para la web las fotos que se dejen en la carpeta fotos-bodega/.

Uso:   ./.venv/bin/python herramientas/procesar_fotos.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "fotos-bodega"
SALIDA = RAIZ / "static" / "img" / "bodega"
EXTENSIONES = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
ANCHO_MAX = 1600


def main() -> int:
    if not ENTRADA.exists():
        print(f"No existe la carpeta {ENTRADA}")
        return 1
    SALIDA.mkdir(parents=True, exist_ok=True)

    fotos = [f for f in sorted(ENTRADA.iterdir())
             if f.suffix.lower() in EXTENSIONES and not f.name.startswith(".")]
    if not fotos:
        print(f"No hay fotos en {ENTRADA}.")
        print("Guarde ahí las fotos (JPG o PNG) y vuelva a ejecutar este programa.")
        return 0

    print(f"Procesando {len(fotos)} foto(s)…\n")
    for f in fotos:
        try:
            im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        except Exception as e:
            print(f"  ✗ {f.name}: no se pudo leer ({e})")
            continue
        original = f"{im.width}x{im.height}"
        if im.width > ANCHO_MAX:
            im.thumbnail((ANCHO_MAX, ANCHO_MAX), Image.LANCZOS)
        destino = SALIDA / (f.stem.lower().replace(" ", "-") + ".jpg")
        im.save(destino, "JPEG", quality=84, optimize=True)
        kb = destino.stat().st_size / 1024
        print(f"  ✓ {f.name}  ({original} → {im.width}x{im.height}, {kb:.0f} KB)")
        print(f"    queda en:  /static/img/bodega/{destino.name}")

    print(f"\nListo. {len(fotos)} foto(s) en {SALIDA}")
    print("Ahora asígnelas desde el panel: Catálogo web → editar producto → Imagen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
