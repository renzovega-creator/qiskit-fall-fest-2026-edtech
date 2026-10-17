"""Proceso del alumno: ejecuta su código y, en modo check, los casos de check.py.

    python -I worker.py learner.py check.py run|check módulos,a,bloquear result.json

Lo lanza qgcheck.runner.grade. Escribe el resultado como JSON en el último argumento.

Antes de ejecutar nada importa las bibliotecas científicas que el código y los casos usan, y crea
`result.json.ready`. El reloj de `grade` empieza con ese archivo: cargar Qiskit no gasta el tiempo
del alumno, que no depende de si el equipo tenía los módulos en caché.
"""
import ast
import contextlib
import importlib
import io
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qgcheck import HelperFailure, last_use, learner, spec  # noqa: E402

CODE_NAME = "tu_codigo.py"
MAX_STDOUT = 10_000
# Solo se precargan estas bibliotecas: el alumno no puede alargar el arranque con un import propio.
PRELOAD_ROOTS = {"qiskit", "qiskit_aer", "qiskit_ibm_runtime", "numpy", "scipy", "matplotlib", "rustworkx", "sympy"}
# Módulos que los ayudantes de qgcheck importan al llamarlos, por el nombre con que check.py los pide.
HELPER_MODULES = {
    "counts": "qiskit.primitives",
    "aer_counts": "qiskit_aer.primitives",
    "state": "qiskit.quantum_info",
    "operator": "qiskit.quantum_info",
}


def imported_modules(source):
    """Módulos que el código importa en cualquier punto, y los que necesitan los ayudantes de qgcheck que pide."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
            if node.module == "qgcheck":
                found.update(HELPER_MODULES[a.name] for a in node.names if a.name in HELPER_MODULES)
            else:
                found.update(f"{node.module}.{a.name}" for a in node.names)
    return found


def preload(*sources):
    """Importa los módulos de PRELOAD_ROOTS que usan los códigos dados. Un fallo lo muestra el código al importar."""
    wanted = set().union(*map(imported_modules, sources))
    for name in sorted(wanted):
        if name.split(".")[0] in PRELOAD_ROOTS:
            with contextlib.suppress(Exception):
                importlib.import_module(name)


def describe(exc, source):
    """Describe el error y, si procede, la última línea del código del alumno."""
    if isinstance(exc, SyntaxError) and exc.filename == CODE_NAME:
        lineno, text = exc.lineno, (exc.text or "").strip()
        return f"{type(exc).__name__}: {exc.msg} (línea {lineno}: {text})"
    lines = source.splitlines()
    where = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == CODE_NAME]
    msg = f"{type(exc).__name__}: {exc}"
    if where:
        n = where[-1].lineno
        text = lines[n - 1].strip() if n <= len(lines) else ""
        return f"{msg} (línea {n}: {text})"
    return msg


def run_case(fn):
    try:
        fn()
    except HelperFailure as exc:
        return f"{exc} Pasó al usar {last_use()}." if last_use() else str(exc)
    except AssertionError as exc:
        return str(exc) or "El caso falló."
    except Exception as exc:
        return f"Tu código lanzó {type(exc).__name__}: {exc}" + (f" Pasó al usar {last_use()}." if last_use() else "")
    return None


def run_cases(check_path):
    tests, hidden = [], 0
    for fn, shown in spec.load_cases(check_path):
        message = run_case(fn)
        if shown is None:
            hidden += 1
        tests.append(
            dict(
                name=shown or f"caso oculto {hidden}",
                visible=shown is not None,
                passed=message is None,
                message=message,
                hint=getattr(fn, "qg_hint", None),
            )
        )
    return tests


def main(learner_path, check_path, mode, block, out):
    for name in filter(None, block.split(",")):
        sys.modules[name] = None
    source = Path(learner_path).read_text(encoding="utf-8")
    preload(source, Path(check_path).read_text(encoding="utf-8"))
    Path(out + ".ready").touch()
    ns = {"__name__": "__main__"}
    buf = io.StringIO()
    error = None
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            exec(compile(source, CODE_NAME, "exec"), ns)
        except BaseException as exc:
            error = describe(exc, source)
    tests = []
    if mode == "check" and error is None:
        learner._bind(ns)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            tests = run_cases(check_path)
    stdout = buf.getvalue()
    if len(stdout) > MAX_STDOUT:
        stdout = stdout[:MAX_STDOUT] + "\n… (salida recortada)"
    passed = error is None and all(t["passed"] for t in tests)
    Path(out).write_text(json.dumps(dict(passed=passed, stdout=stdout, error=error, tests=tests)), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:])
