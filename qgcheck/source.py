"""Lo que el corrector sabe del código de un alumno antes de ejecutarlo.

`preload` importa las bibliotecas científicas que ese código y los casos usan, para que los
procesos que se bifurcan después las hereden ya cargadas. `describe` da el error de una ejecución
con la línea del alumno.
"""

import ast
import contextlib
import importlib
import traceback

CODE_NAME = "tu_codigo.py"
# Solo se precargan estas bibliotecas: el alumno no puede alargar el arranque con un import propio.
PRELOAD_ROOTS = {
    "qiskit",
    "qiskit_aer",
    "qiskit_ibm_runtime",
    "numpy",
    "scipy",
    "matplotlib",
    "rustworkx",
    "sympy",
}
# Módulos que los ayudantes de qgcheck importan al llamarlos, por el nombre con que check.py los pide.
HELPER_MODULES = {
    "counts": "qiskit.primitives",
    "aer_counts": "qiskit_aer.primitives",
    "state": "qiskit.quantum_info",
    "operator": "qiskit.quantum_info",
}
# Funciones de qiskit que importan scipy.stats al primer uso. Precargarlo evita que el comprobador y el
# proceso del alumno lo importen cada uno (0,5 s de CPU en el corredor).
USES_SCIPY_STATS = {"random_unitary", "random_hermitian", "random_quantum_channel", "QuantumVolume"}


def imported_modules(source: str) -> set[str]:
    """Módulos que el código importa en cualquier punto, y los que necesitan los ayudantes de qgcheck que pide."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if {
            getattr(node, "id", None),
            getattr(node, "attr", None),
            getattr(node, "name", None),
        } & USES_SCIPY_STATS:
            found.add("scipy.stats")
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
            if node.module == "qgcheck":
                found.update(HELPER_MODULES[a.name] for a in node.names if a.name in HELPER_MODULES)
            else:
                found.update(f"{node.module}.{a.name}" for a in node.names)
    return found


def uses_inside(check_source: str) -> bool:
    """Si `check.py` define alguna función marcada con `@inside`, que corre en el proceso del alumno."""
    try:
        tree = ast.parse(check_source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                if getattr(target, "id", getattr(target, "attr", None)) == "inside":
                    return True
    return False


def preload(*sources: str) -> None:
    """Importa los módulos de PRELOAD_ROOTS que usan los códigos dados. Un fallo lo muestra el código al importar."""
    wanted = set().union(*map(imported_modules, sources))
    for name in sorted(wanted):
        if name.split(".")[0] in PRELOAD_ROOTS:
            with contextlib.suppress(Exception):
                importlib.import_module(name)


def describe(exc: BaseException, source: str) -> str:
    """Describe el error y, si procede, la última línea del código del alumno."""
    if isinstance(exc, SyntaxError) and exc.filename == CODE_NAME:
        lineno, text = exc.lineno, (exc.text or "").strip()
        return f"{type(exc).__name__}: {exc.msg} (línea {lineno}: {text})"
    lines = source.splitlines()
    where = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == CODE_NAME]
    msg = f"{type(exc).__name__}: {exc}"
    n = where[-1].lineno if where else None
    if n is not None:
        text = lines[n - 1].strip() if n <= len(lines) else ""
        return f"{msg} (línea {n}: {text})"
    return msg
