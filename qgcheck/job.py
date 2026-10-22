"""Proceso de un trabajo: ejecuta el código del alumno o lo comprueba con un ejercicio.

    python -u -P -m qgcheck.job run CÓDIGO
    python -u -P -m qgcheck.job check CÓDIGO CHECK.PY

Escribe en el descriptor QG_REPORT_FD un JSON `{"error": texto o null, "tests": [...]}` con la forma
que `qgcheck.grade` da a esos campos. `QG_BLOCK` lista, separados por comas, módulos que no se pueden
importar.

`run` ejecuta el código en este proceso. `check` importa las bibliotecas que el código y los casos
usan, bifurca el proceso del alumno (`qgcheck.host`) con ellas ya cargadas y corre aquí los casos de
`check.py`. `qgcheck.learner` se enlaza a un espacio de nombres cuyas funciones son llamadas a ese
proceso, así que el código del alumno nunca comparte proceso, canal ni estado con los casos. Entre
procesos solo viajan datos (`qgcheck.wire`).
"""

import sys

# Qiskit Runtime y Mitigation cargan scipy y sus clientes al importarse y casi nadie los usa en un
# caso. Con `all` sin filtro, Qiskit falla (`n_local` no tiene `__all__`).
LAZY_IMPORTERS = ("qiskit_ibm_runtime", "qiskit_mitigation")


def _lazy(importer: str | None, name: str, fromlist: tuple[str, ...] | None) -> bool:
    return importer is not None and importer.startswith(LAZY_IMPORTERS)


sys.set_lazy_imports_filter(_lazy)
sys.set_lazy_imports("all")

import ctypes  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import secrets  # noqa: E402
import socket  # noqa: E402
import traceback  # noqa: E402
import warnings  # noqa: E402
from collections.abc import Callable, Sequence  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, cast  # noqa: E402

from qgcheck import HelperFailure, LearnerError, _note_use, last_use, learner, spec  # noqa: E402
from qgcheck.host import serve  # noqa: E402
from qgcheck.source import CODE_NAME, describe, preload  # noqa: E402
from qgcheck.wire import BROKEN, WireError, decode, encode, receive, send  # noqa: E402

# Los hilos de BLAS y de matplotlib hacen que Python avise de cada fork, y el aviso llegaría a la
# salida del alumno.
warnings.filterwarnings("ignore", message=".*multi-threaded.*fork", category=DeprecationWarning)

PR_SET_DUMPABLE = 4
REPLY_KEYS = {"id", "value", "raised", "error", "used"}


class Host:
    """Cliente del proceso del alumno."""

    def __init__(self, code_path: str, check_path: str) -> None:
        self._sock, theirs = socket.socketpair()
        self._pid = os.fork()
        if self._pid == 0:
            try:
                self._sock.close()
                serve(theirs, code_path, check_path)
            except BaseException:
                traceback.print_exc()
            finally:
                os._exit(0)
        theirs.close()
        self._broken = False

    def stop(self) -> None:
        self._sock.close()
        os.kill(self._pid, 9)
        os.waitpid(self._pid, 0)

    def request(
        self,
        op: str,
        name: str | None = None,
        args: Sequence[Any] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        """Devuelve el valor de la petición; un fallo del alumno se lanza como en el caso."""
        if self._broken:
            raise AssertionError(BROKEN)
        try:
            reply = self._exchange(
                {
                    "op": op,
                    "name": name,
                    "args": encode(list(args)),
                    "kwargs": encode(kwargs or {}),
                }
            )
            if isinstance(reply.get("used"), str):
                _note_use(reply["used"])
            if "error" in reply:
                raise AssertionError(str(reply["error"]))
            if "raised" in reply:
                kind, text = reply["raised"]
                if kind == "AssertionError":
                    raise AssertionError(str(text))
                raise LearnerError(f"{kind}: {text}")
            return self._decode(reply["value"])
        except AssertionError, LearnerError:
            raise
        except WireError, KeyError, TypeError, ValueError, RecursionError, ImportError, OSError:
            self._broken = True
            raise AssertionError(BROKEN) from None

    def _decode(self, value: Any) -> Any:
        """Un dato del alumno que no se reconstruye (p. ej. un `Statevector` cuyas dimensiones no
        cuadran, que lanza `QiskitError`) es un canal roto, no una excepción de su código."""
        try:
            return decode(value)
        except Exception:
            self._broken = True
            raise AssertionError(BROKEN) from None

    def _exchange(self, message: dict[str, Any]) -> dict[str, Any]:
        """Envía la petición con un `id` que el alumno no puede adivinar y lee su respuesta.

        El proceso del alumno no conoce el `id` antes de recibir la petición, así que no puede dejar
        escritas respuestas que este lado tome por las de peticiones futuras.
        """
        ident = secrets.token_hex(16)
        send(self._sock.fileno(), message | {"id": ident})
        reply = receive(self._sock.fileno())
        valid = (
            reply.get("id") == ident
            and len(reply.keys() & {"value", "raised", "error"}) == 1
            and reply.keys() <= REPLY_KEYS
        )
        if not valid:
            raise WireError("respuesta inválida")
        return reply


class Names:
    """El espacio de nombres que lee `qgcheck.learner`.

    `kinds` dice qué nombres definió el alumno y cuáles son funciones o clases. Una función es una
    llamada al proceso del alumno; el valor de otro nombre se pide una vez.
    """

    def __init__(self, host: Host, kinds: Any) -> None:
        if not (
            isinstance(kinds, dict)
            and all(isinstance(k, str) and isinstance(v, bool) for k, v in kinds.items())
        ):
            raise AssertionError(BROKEN)
        self._host, self._kinds = host, kinds
        self._values: dict[str, Any] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._kinds

    def __getitem__(self, name: str) -> Any:
        if self._kinds[name]:

            def call(*args: Any, **kwargs: Any) -> Any:
                return self._host.request("call", name, args, kwargs)

            return call
        if name not in self._values:
            self._values[name] = self._host.request("get", name)
        return self._values[name]


def run_case(fn: Callable[[], object]) -> str | None:
    try:
        fn()
    except HelperFailure as exc:
        return f"{exc} Pasó al usar {last_use()}." if last_use() else str(exc)
    except AssertionError as exc:
        return str(exc) or "El caso falló."
    except Exception as exc:
        what = str(exc) if isinstance(exc, LearnerError) else f"{type(exc).__name__}: {exc}"
        return f"Tu código lanzó {what}" + (f" Pasó al usar {last_use()}." if last_use() else "")
    return None


def run_cases(check_path: str) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    hidden = 0
    for fn, shown in spec.load_cases(Path(check_path)):
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


def run(code_path: str) -> dict[str, Any]:
    source = Path(code_path).read_text(encoding="utf-8")
    try:
        exec(compile(source, CODE_NAME, "exec"), {"__name__": "__main__"})
    except BaseException as e:
        return {"error": describe(e, source), "tests": []}
    return {"error": None, "tests": []}


def check(code_path: str, check_path: str) -> dict[str, Any]:
    # Mismo uid que el alumno: sin esto podría leer o escribir la memoria de este proceso. Los
    # procesos del alumno heredan la marca.
    ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    preload(
        Path(code_path).read_text(encoding="utf-8"), Path(check_path).read_text(encoding="utf-8")
    )
    host = Host(code_path, check_path)
    try:
        try:
            names = Names(host, host.request("names"))
        except AssertionError as e:
            return {"error": str(e), "tests": []}
        learner._bind(
            names, remote=lambda name, args, kwargs: host.request("inside", name, args, kwargs)
        )
        return {"error": None, "tests": run_cases(check_path)}
    finally:
        host.stop()


def main(mode: str, code_path: str, check_path: str = "") -> None:
    for name in filter(None, os.environ.get("QG_BLOCK", "").split(",")):
        cast("dict[str, Any]", sys.modules)[name] = None
    report = check(code_path, check_path) if mode == "check" else run(code_path)
    with os.fdopen(int(os.environ["QG_REPORT_FD"]), "w") as f:
        json.dump(report, f)
    if mode == "check":
        # El comprobador no tiene nada que cerrar; cerrar el intérprete con Qiskit cargado cuesta 0,1 s.
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main(*sys.argv[1:])
