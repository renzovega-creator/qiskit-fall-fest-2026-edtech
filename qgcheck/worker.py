"""Proceso del alumno: ejecuta su código y, en modo check, los casos de check.py.

    python -I worker.py learner.py check.py run|check módulos,a,bloquear result.json

Lo lanza qgcheck.runner.grade. Escribe el resultado como JSON en el último argumento.
"""
import contextlib
import io
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qgcheck import learner, spec  # noqa: E402

CODE_NAME = "tu_codigo.py"
MAX_STDOUT = 10_000


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
    except AssertionError as exc:
        return str(exc) or "El caso falló."
    except Exception as exc:
        return f"Tu código lanzó {type(exc).__name__}: {exc}"
    return None


def main(learner_path, check_path, mode, block, out):
    for name in filter(None, block.split(",")):
        sys.modules[name] = None
    source = Path(learner_path).read_text(encoding="utf-8")
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
        hidden = 0
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            for fn, shown in spec.load_cases(check_path):
                message = run_case(fn)
                if shown is None:
                    hidden += 1
                tests.append(dict(name=shown or f"caso oculto {hidden}", visible=shown is not None,
                                  passed=message is None, message=message))
    stdout = buf.getvalue()
    if len(stdout) > MAX_STDOUT:
        stdout = stdout[:MAX_STDOUT] + "\n… (salida recortada)"
    passed = error is None and all(t["passed"] for t in tests)
    Path(out).write_text(json.dumps(dict(passed=passed, stdout=stdout, error=error, tests=tests)), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:])
