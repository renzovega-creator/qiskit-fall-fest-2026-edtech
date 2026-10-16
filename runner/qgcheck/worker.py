"""Intermediario entre el comprobador y el código del alumno.

    python -u -P -m qgcheck.worker CÓDIGO FD_PETICIONES FD_RESPUESTAS

Este proceso nunca ejecuta código del alumno. Por cada petición
`{"name", "args", "kwargs"}` hace un `fork`; el hijo cierra todos los
descriptores salvo un pipe propio de esa llamada, ejecuta el código, llama a la
función y escribe un solo mensaje, `{"value": ...}` o `{"error": ...}`. El
intermediario lo lee, mata al hijo y lo reenvía por el canal del comprobador,
que el alumno nunca tiene abierto. Lo que el alumno controla es el valor de su
propia llamada y nada más. Cada llamada ejecuta el código desde cero; la salida
de la carga solo se muestra en la primera. Termina cuando el comprobador cierra
el canal.
"""
import contextlib
import ctypes
import os
import runpy
import signal
import sys
import traceback

from qgcheck.wire import BROKEN, WireError, decode, encode, receive, send

MESSAGE_CAP = 300
PR_SET_DUMPABLE = 4


def failure(text):
    return {"error": text[:MESSAGE_CAP]}


def answer(namespace, request):
    name = request.get("name")
    if name not in namespace:
        return failure(f"Falta `{name}` en tu código.")
    fn = namespace[name]
    if not callable(fn):
        return failure(f"`{name}` debe ser una función.")
    try:
        value = fn(*decode(request.get("args", [])), **decode(request.get("kwargs", {})))
    except BaseException as e:
        traceback.print_exc(file=sys.stderr)
        return failure(f"{type(e).__name__}: {e}")
    try:
        return {"value": encode(value)}
    except TypeError as e:
        return failure(f"`{name}` devolvió {e} que no se puede comprobar.")


def call_in_child(path, request, fd, quiet_load):
    """Cuerpo del hijo: solo conserva `fd`, el extremo de escritura de su llamada."""
    os.closerange(3, fd)
    os.closerange(fd + 1, 4096)
    try:
        with contextlib.ExitStack() as stack:
            if quiet_load:
                devnull = stack.enter_context(open(os.devnull, "w"))
                stack.enter_context(contextlib.redirect_stdout(devnull))
                stack.enter_context(contextlib.redirect_stderr(devnull))
            namespace = runpy.run_path(path, run_name="learner")
    except BaseException as e:
        traceback.print_exc(file=sys.stderr)
        message = failure(f"Tu código falló al ejecutarse: {type(e).__name__}: {e}")
    else:
        message = answer(namespace, request)
    try:
        send(fd, message)
    except WireError:
        pass
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def run_call(path, request, quiet_load):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        call_in_child(path, request, write_fd, quiet_load)
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


def main():
    path, requests, responses = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    # Mismo uid que el alumno: sin esto podría leer o escribir la memoria de este
    # proceso. El hijo hereda la marca.
    ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    import qiskit  # noqa: F401  Los hijos lo heredan ya cargado.

    first = True
    while True:
        try:
            request = receive(requests)
        except WireError:
            return
        send(responses, run_call(path, request, quiet_load=not first))
        first = False


if __name__ == "__main__":
    try:
        main()
    except WireError:
        pass
    os._exit(0)
