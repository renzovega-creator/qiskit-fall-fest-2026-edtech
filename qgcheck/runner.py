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

`timeout` mide la ejecución del código y de los casos. El proceso importa antes las bibliotecas que
ese código usa (ver worker.py) y ese arranque, que depende de la caché del equipo, tiene su tope
aparte, STARTUP.

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
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from qgcheck import spec

MAX_CODE = 20_000
TIMEOUT = 10
STARTUP = 60
POLL = 0.02
WORKER = Path(__file__).with_name("worker.py")


def _wait(proc: subprocess.Popen[bytes], ready: Path, timeout: float) -> bool:
    """Espera a que termine el proceso. Devuelve False si agotó el arranque o el tiempo del código.

    El worker importa Qiskit y crea `ready` antes de ejecutar el código del alumno; los `timeout`
    segundos cuentan desde ese archivo, y el arranque tiene su propio tope, STARTUP.
    """
    launched = time.monotonic()
    started = None
    while True:
        try:
            proc.wait(timeout=POLL)
            return True
        except subprocess.TimeoutExpired:
            pass
        now = time.monotonic()
        if started is None and ready.exists():
            started = now
        if now > (started + timeout if started else launched + STARTUP):
            return False


def _answer(error: str, t0: float, stdout: str = "") -> dict[str, Any]:
    return dict(
        passed=False, stdout=stdout, error=error, tests=[], ms=round((time.monotonic() - t0) * 1000)
    )


def grade(
    exercise_id: str,
    code: str,
    mode: str = "check",
    block: Iterable[str] = (),
    timeout: float = TIMEOUT,
) -> dict[str, Any]:
    t0 = time.monotonic()
    if mode not in ("run", "check"):
        raise ValueError(f"modo inválido: {mode!r}")
    d = spec.folder(exercise_id)
    if not d.is_dir():
        raise ValueError(f"ejercicio desconocido: {exercise_id!r}")
    if len(code.encode("utf-8")) > MAX_CODE:
        return _answer(f"El código supera {MAX_CODE // 1000} KB.", t0)
    with tempfile.TemporaryDirectory(prefix="qg-") as tmp_name:
        tmp = Path(tmp_name)
        (tmp / "learner.py").write_text(code, encoding="utf-8")
        out = tmp / "result.json"
        ready = tmp / "result.json.ready"
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp), "MPLBACKEND": "Agg"}
        with open(tmp / "stderr.txt", "w+", encoding="utf-8", errors="replace") as errors:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    str(WORKER),
                    str(tmp / "learner.py"),
                    str(d / "check.py"),
                    mode,
                    ",".join(block),
                    str(out),
                ],
                cwd=tmp,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=errors,
                start_new_session=True,
            )
            if not _wait(proc, ready, timeout):
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                if ready.exists():
                    return _answer(f"Tu código tardó más de {timeout} s y se detuvo.", t0)
                return _answer(f"El corredor tardó más de {STARTUP} s en arrancar.", t0)
            errors.seek(0)
            err = errors.read()
        if not out.exists():
            # Sin resultado, el proceso terminó antes de completar la ejecución.
            return _answer(
                "El código no terminó: se quedó sin memoria o el proceso se cerró.", t0, err[-500:]
            )
        result: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
    result["ms"] = round((time.monotonic() - t0) * 1000)
    return result
