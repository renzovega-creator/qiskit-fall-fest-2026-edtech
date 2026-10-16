"""Comprueba los cuadernos marimo de practica/.

    uv run python tools/practica.py [cuaderno ...]

Cada cuaderno se ejecuta tal cual y con las soluciones de
practica/soluciones/<nombre>.json aplicadas. Las comprobaciones deben dar ✅ con las soluciones.
Si tiene controles mo.ui.slider o mo.ui.number, también se ejecuta con todos los controles en su
mínimo y en su máximo. Las comprobaciones que dan ❌ en un extremo se listan, pero no hacen fallar
la ejecución porque pueden depender de los parámetros.
"""
import ast
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


def ejecutar(src, nombre, carpeta):
    """Ejecuta src como cuaderno `nombre` con los módulos de `carpeta` disponibles."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / nombre
        tmp.write_text(src, encoding="utf-8")
        return veredictos(tmp, carpeta)


def con_extremo(src, extremo):
    """Sustituye el value= de cada control por su mínimo o máximo.

    Devuelve el código actualizado y los valores usados por nombre de control.
    """
    lineas = src.encode("utf-8").split(b"\n")
    inicios = [0]
    for linea in lineas:
        inicios.append(inicios[-1] + len(linea) + 1)
    pos = lambda lineno, col: inicios[lineno - 1] + col
    cambios, valores = [], {}
    for asig in ast.walk(ast.parse(src)):
        call = getattr(asig, "value", None)
        if not (isinstance(asig, ast.Assign) and isinstance(call, ast.Call)
                and ast.unparse(call.func) in ("mo.ui.slider", "mo.ui.number")):
            continue
        nombre = ast.unparse(asig.targets[0])
        kw = {k.arg: k.value for k in call.keywords}
        limites = [ast.literal_eval(a) for a in call.args[:2]]
        limites += [ast.literal_eval(kw[k]) for k in ("start", "stop")[len(limites):]]
        if "value" not in kw:
            raise ValueError(f"{nombre}: el control no fija value=")
        valor = limites[0 if extremo == "min" else 1]
        v = kw["value"]
        cambios.append((pos(v.lineno, v.col_offset), pos(v.end_lineno, v.end_col_offset), repr(valor)))
        valores[nombre] = valor
    datos = src.encode("utf-8")
    for a, b, nuevo in sorted(cambios, reverse=True):
        datos = datos[:a] + nuevo.encode("utf-8") + datos[b:]
    return datos.decode("utf-8"), valores


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
    carpeta = f.resolve().parent
    try:
        con = ejecutar(src, f.name, carpeta)
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
    for extremo in ("min", "max"):
        try:
            nuevo, valores = con_extremo(src, extremo)
            if not valores:
                break
            ext = ejecutar(nuevo, f.name, carpeta)
        except Exception as e:
            print(f"✗ {rel}: error en {extremo} con soluciones: {e!r}")
            fallos += 1
            continue
        malos = [m for s, m in ext if s == "❌"]
        if malos:
            print(f"! {rel}: ❌ en {extremo} con {valores}: {malos}")
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
