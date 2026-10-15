"""Comprueba los cuadernos marimo de practica/.

    uv run python tools/practica.py [cuaderno ...]

Cada cuaderno se ejecuta dos veces: tal cual (debe correr sin errores) y con las soluciones
de practica/soluciones/<nombre>.json aplicadas (todas las comprobaciones deben dar ✅).
"""
import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PR = ROOT / "practica"


def veredictos(path, carpeta):
    """Ejecuta el cuaderno con sus módulos vecinos disponibles para importar."""
    sys.path.insert(0, str(carpeta))
    try:
        spec = importlib.util.spec_from_file_location("nb_" + path.stem, path)
        nb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nb)
        with contextlib.redirect_stdout(io.StringIO()):
            outputs, _ = nb.app.run()
    finally:
        sys.path.remove(str(carpeta))
    text = " ".join(str(getattr(o, "text", o)) for o in outputs)
    return re.findall(r"(✅|❌)\s+([^<&]{0,60})", text)


def comprobar(f):
    """Devuelve 1 si el cuaderno falla, 0 si pasa o no tiene soluciones."""
    rel = f.resolve().relative_to(PR.resolve()).as_posix()
    try:
        sin = veredictos(f, f.resolve().parent)
    except Exception as e:
        print(f"✗ {rel}: error sin resolver: {e!r}")
        return 1
    solf = PR / "soluciones" / (rel.replace("/", "__").replace(".py", ".json"))
    if not solf.exists():
        print(f"? {rel}: sin soluciones ({len(sin)} comprobaciones)")
        return 0
    fallos = 0
    src = f.read_text(encoding="utf-8")
    for old, new in json.loads(solf.read_text(encoding="utf-8")):
        if old not in src:
            print(f"✗ {rel}: la solución no encuentra «{old}»")
            fallos += 1
        src = src.replace(old, new)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / f.name
        tmp.write_text(src, encoding="utf-8")
        try:
            con = veredictos(tmp, f.resolve().parent)
        except Exception as e:
            print(f"✗ {rel}: error con soluciones: {e!r}")
            return fallos + 1
    malos = [m for s, m in con if s == "❌"]
    pend = sum(1 for s, _ in sin if s == "❌")
    if malos:
        print(f"✗ {rel}: con soluciones aún falla: {malos}")
        fallos += 1
    else:
        print(f"✓ {rel}: {pend} misiones pendientes sin resolver, todas ✅ con soluciones")
    return fallos


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")  # Evita que Tk libere figuras desde otro hilo y aborte el proceso.
    files = [Path(a) for a in sys.argv[1:]] or sorted(p for p in PR.rglob("*.py") if "soluciones" not in p.parts)
    fallos = sum(comprobar(f) for f in files)
    print("fallos:", fallos)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
