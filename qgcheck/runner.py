"""Corre el código de un alumno contra un ejercicio, en un proceso aparte.

    from qgcheck import grade
    grade("p1-quickstart/ghz", codigo, mode="check")

El resultado:

    {"passed": bool, "stdout": str, "error": str | None, "ms": int,
     "tests": [{"name": str, "visible": bool, "passed": bool, "message": str | None,
                "hint": int | None}]}

`mode="run"` solo ejecuta el código y devuelve su salida; `tests` queda vacío.
`mode="check"` además corre los casos de check.py. Con `block` los módulos nombrados no se pueden
importar en el proceso del alumno.

El proceso aparte limita el tiempo y mantiene el intérprete del alumno lejos del que llama; no es
un aislamiento de seguridad. Quien exponga esto en red debe correrlo en un contenedor sin red,
con memoria y procesos limitados.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from qgcheck import spec

MAX_CODE = 20_000
TIMEOUT = 10
WORKER = Path(__file__).with_name("worker.py")


def _answer(error, t0, stdout=""):
    return dict(passed=False, stdout=stdout, error=error, tests=[], ms=round((time.monotonic() - t0) * 1000))


def grade(exercise_id, code, mode="check", block=(), timeout=TIMEOUT):
    t0 = time.monotonic()
    if mode not in ("run", "check"):
        raise ValueError(f"modo inválido: {mode!r}")
    d = spec.folder(exercise_id)
    if not d.is_dir():
        raise ValueError(f"ejercicio desconocido: {exercise_id!r}")
    if len(code.encode("utf-8")) > MAX_CODE:
        return _answer(f"El código supera {MAX_CODE // 1000} KB.", t0)
    with tempfile.TemporaryDirectory(prefix="qg-") as tmp:
        tmp = Path(tmp)
        (tmp / "learner.py").write_text(code, encoding="utf-8")
        out = tmp / "result.json"
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp), "MPLBACKEND": "Agg"}
        proc = subprocess.Popen(
            [sys.executable, "-I", str(WORKER), str(tmp / "learner.py"), str(d / "check.py"), mode, ",".join(block), str(out)],
            cwd=tmp, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            start_new_session=True, text=True)
        try:
            _, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return _answer(f"Tu código tardó más de {timeout} s y se detuvo.", t0)
        if not out.exists():
            # Sin resultado, el proceso terminó antes de completar la ejecución.
            return _answer("El código no terminó: se quedó sin memoria o el proceso se cerró.", t0, err[-500:])
        result = json.loads(out.read_text(encoding="utf-8"))
    result["ms"] = round((time.monotonic() - t0) * 1000)
    return result
