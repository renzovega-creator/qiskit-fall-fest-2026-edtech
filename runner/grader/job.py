"""Proceso de un trabajo: ejecuta el código del alumno o lo comprueba con un ejercicio.

    python -u -P -m grader.job run CÓDIGO
    python -u -P -m grader.job check CÓDIGO CHECK.PY

Escribe en el descriptor QG_REPORT_FD un JSON `{"error": texto o null, "tests":
[...]}` con la forma que `qgcheck.grade` da a esos campos.

`run` ejecuta el código en este proceso. `check` lanza `grader.broker`, que
ejecuta el código del alumno en otros procesos, y corre los casos de `check.py`
aquí. `qgcheck.learner` se enlaza a un espacio de nombres cuyas funciones son
llamadas al intermediario, así que el código del alumno nunca comparte proceso,
canal ni estado con los casos. Entre procesos solo viajan datos (`wire.py`).
"""
import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path

from grader.wire import BROKEN, WireError, decode, encode, receive, send
from qgcheck import learner, spec
from qgcheck.worker import CODE_NAME, describe, run_case

PR_SET_DUMPABLE = 4


class Broker:
    """Cliente del intermediario del alumno."""

    def __init__(self, path):
        requests_r, self._requests = os.pipe()
        self._responses, responses_w = os.pipe()
        env = {k: v for k, v in os.environ.items() if not k.startswith("QG_")}
        self._proc = subprocess.Popen(
            [sys.executable, "-u", "-P", "-m", "grader.broker", path, str(requests_r), str(responses_w)],
            env=env, pass_fds=(requests_r, responses_w),
        )
        os.close(requests_r)
        os.close(responses_w)
        self._broken = False

    def stop(self):
        os.close(self._requests)
        os.close(self._responses)
        self._proc.kill()
        self._proc.wait()

    def request(self, op, name=None, args=(), kwargs=None):
        """Devuelve el valor de la petición; el texto del fallo es el de un `AssertionError`."""
        if self._broken:
            raise AssertionError(BROKEN)
        try:
            send(self._requests, {"op": op, "name": name, "args": encode(list(args)), "kwargs": encode(kwargs or {})})
            reply = receive(self._responses)
            if "error" in reply:
                raise AssertionError(str(reply["error"]))
            return decode(reply["value"])
        except AssertionError:
            raise
        except (WireError, KeyError, TypeError, ValueError, RecursionError, ImportError):
            self._broken = True
            raise AssertionError(BROKEN)


class Names:
    """El espacio de nombres que lee `qgcheck.learner`.

    `kinds` dice qué nombres definió el alumno y cuáles son funciones. Una función
    es una llamada al intermediario; el valor de otro nombre se pide una vez.
    """

    def __init__(self, broker, kinds):
        if not (isinstance(kinds, dict) and all(isinstance(k, str) and isinstance(v, bool) for k, v in kinds.items())):
            raise AssertionError(BROKEN)
        self._broker, self._kinds, self._values = broker, kinds, {}

    def __contains__(self, name):
        return name in self._kinds

    def __getitem__(self, name):
        if self._kinds[name]:
            return lambda *args, **kwargs: self._broker.request("call", name, args, kwargs)
        if name not in self._values:
            self._values[name] = self._broker.request("get", name)
        return self._values[name]


def run(code_path):
    source = Path(code_path).read_text(encoding="utf-8")
    try:
        exec(compile(source, CODE_NAME, "exec"), {"__name__": "__main__"})
    except BaseException as e:
        return {"error": describe(e, source), "tests": []}
    return {"error": None, "tests": []}


def check(code_path, check_path):
    broker = Broker(code_path)
    try:
        try:
            names = Names(broker, broker.request("names"))
        except AssertionError as e:
            return {"error": str(e), "tests": []}
        learner._bind(names)
        tests, hidden = [], 0
        for fn, shown in spec.load_cases(check_path):
            message = run_case(fn)
            if shown is None:
                hidden += 1
            tests.append(dict(name=shown or f"caso oculto {hidden}", visible=shown is not None,
                              passed=message is None, message=message))
        return {"error": None, "tests": tests}
    finally:
        broker.stop()


def main(mode, code_path, check_path=None):
    if mode == "check":
        # Mismo uid que el alumno: sin esto podría leer o escribir la memoria de este proceso.
        ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
        report = check(code_path, check_path)
    else:
        report = run(code_path)
    with os.fdopen(int(os.environ["QG_REPORT_FD"]), "w") as f:
        json.dump(report, f)


if __name__ == "__main__":
    main(*sys.argv[1:])
