"""Prepara el curso activo para GitHub Pages: python tools/pages.py shots/pages."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
NOTICE = (
    '<p role="note" style="padding:12px 16px;border:1px solid var(--line);'
    'border-radius:8px;background:var(--bg2);color:var(--ink);font:14px/1.5 var(--sans)">'
    "<strong>Demo estática en GitHub Pages.</strong> Puedes recorrer las lecciones y ver "
    "el perfil de ejemplo con resultados precomputados de Qiskit. Esta publicación no "
    "ejecuta código nuevo ni ofrece cuentas. "
    '<a href="juego.html#ejemplo" style="color:var(--acc);font-weight:600">'
    "Ver resultados de ejemplo →</a></p>"
)


def build(destination: Path) -> None:
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit("La carpeta de salida debe estar vacía.")
    destination.mkdir(parents=True, exist_ok=True)
    course = json.loads((SITE / "course.json").read_text(encoding="utf-8"))
    for item in SITE.iterdir():
        if item.is_file():
            shutil.copy2(item, destination / item.name)
        elif item.is_dir() and item.name != "lessons":
            shutil.copytree(item, destination / item.name)
    for part in course["parts"]:
        for lesson in part["lessons"]:
            name = lesson["id"]
            shutil.copytree(SITE / "lessons" / name, destination / "lessons" / name)
    # Las páginas llaman a esta interfaz aunque no haya proveedor de cuentas.
    (destination / "account.js").write_text(
        "window.QGAccount = { ready: Promise.resolve(), changed() {} };\n",
        encoding="utf-8",
    )
    for name, anchor in (
        ("index.html", '<div class="next" id="next"></div>'),
        ("juego.html", '<main id="vista" tabindex="-1"></main>'),
        ("lesson.html", '<div class="actions">'),
    ):
        page = destination / name
        source = page.read_text(encoding="utf-8")
        if anchor not in source:
            raise SystemExit(f"No se encuentra el punto de inserción en {name}.")
        page.write_text(source.replace(anchor, NOTICE + "\n" + anchor, 1), encoding="utf-8")
    (destination / ".nojekyll").touch()
    print(f"GitHub Pages: {destination}")
    print(f"Lecciones: {sum(len(p['lessons']) for p in course['parts'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    build(parser.parse_args().destination)
