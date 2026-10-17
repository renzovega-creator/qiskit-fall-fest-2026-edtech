"""Intermediario entre el comprobador y el código del alumno.

    python -u -P -m grader.broker CÓDIGO FD_PETICIONES FD_RESPUESTAS

Este proceso nunca ejecuta código del alumno. Cada petición es `{"op": ...}`:
`names` pide qué nombres definió el código y si son funciones, `get` pide el
valor de `name` y `call` el de `name(*args, **kwargs)`. Por cada petición hace
un `fork`; el hijo cierra todos los descriptores salvo un pipe propio de esa
petición, ejecuta el código desde cero, responde y escribe un solo mensaje,
`{"value": ...}` o `{"error": ...}`. El intermediario lo lee, mata al hijo y lo
reenvía por el canal del comprobador, que el alumno nunca tiene abierto. Lo que
el alumno controla es el valor de su propia petición y nada más. La salida del
código solo se muestra en la primera petición. Termina cuando el comprobador
cierra el canal.
"""

import contextlib
import ctypes
import os
import signal
import sys
from pathlib import Path
from typing import Any

from grader.wire import BROKEN, WireError, decode, encode, receive, send

from qgcheck.worker import CODE_NAME, describe

MESSAGE_CAP = 300
PR_SET_DUMPABLE = 4


def failure(text: str) -> dict[str, Any]:
    return {"error": text[:MESSAGE_CAP]}


def answer(namespace: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    op, name = request.get("op"), request.get("name")
    if op == "names":
        return {
            "value": encode(
                {n: callable(v) for n, v in namespace.items() if not n.startswith("__")}
            )
        }
    if name not in namespace:
        return failure(f"Falta definir `{name}` en tu código.")
    value = namespace[name]
    if op == "call":
        if not callable(value):
            return failure(f"`{name}` debe ser una función.")
        try:
            value = value(*decode(request.get("args", [])), **decode(request.get("kwargs", {})))
        except Exception as e:
            return failure(f"Tu código lanzó {type(e).__name__}: {e}")
    try:
        return {"value": encode(value)}
    except TypeError as e:
        return failure(f"`{name}` contiene {e} que no se puede comprobar.")


def call_in_child(source: str, request: dict[str, Any], fd: int, quiet_load: bool) -> None:
    """Cuerpo del hijo: solo conserva `fd`, el extremo de escritura de su llamada."""
    os.closerange(3, fd)
    os.closerange(fd + 1, 4096)
    namespace: dict[str, Any] = {"__name__": "__main__"}
    try:
        with contextlib.ExitStack() as stack:
            if quiet_load:
                devnull = stack.enter_context(open(os.devnull, "w"))
                stack.enter_context(contextlib.redirect_stdout(devnull))
                stack.enter_context(contextlib.redirect_stderr(devnull))
            exec(compile(source, CODE_NAME, "exec"), namespace)
    except BaseException as e:
        message = failure(describe(e, source))
    else:
        message = answer(namespace, request)
    with contextlib.suppress(WireError):
        send(fd, message)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def run_call(source: str, request: dict[str, Any], quiet_load: bool) -> dict[str, Any]:
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        call_in_child(source, request, write_fd, quiet_load)
    os.close(write_fd)
    try:
        reply = receive(read_fd)
    except WireError:
        reply = failure(BROKEN)
    finally:
        os.close(read_fd)
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    if isinstance(reply.get("error"), str):
        return failure(reply["error"])
    if "value" in reply and len(reply) == 1:
        return reply
    return failure(BROKEN)


def main() -> None:
    path, requests, responses = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    # Mismo uid que el alumno: sin esto podría leer o escribir la memoria de este
    # proceso. El hijo hereda la marca.
    ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    import qiskit  # noqa: F401  Los hijos lo heredan ya cargado.

    source = Path(path).read_text(encoding="utf-8")
    first = True
    while True:
        try:
            request = receive(requests)
        except WireError:
            return
        send(responses, run_call(source, request, quiet_load=not first))
        first = False


if __name__ == "__main__":
    with contextlib.suppress(WireError):
        main()
    os._exit(0)
