"""Ayudas para los `check.py` de los ejercicios.

    from qgcheck import learner, counts, visible

    ghz = learner.ghz

    @visible("n = 2, 3 y 4")
    def test_small():
        assert set(counts(ghz(3))) == {"000", "111"}, "con n = 3 no salen solo 000 y 111"

`learner.nombre` llama a la función `nombre` del código del alumno. El código
corre en procesos aparte (ver `worker.py`) que solo intercambian datos con el
comprobador (ver `wire.py`), así que no pueden tocar su estado ni su canal. Un
nombre que falta, o un código que falló al ejecutarse, hace fallar la llamada
con un mensaje en español.
"""
import os
import subprocess
import sys

from qgcheck.wire import BROKEN, WireError, decode, encode, receive, send

MESSAGE_CAP = 300


class LearnerError(AssertionError):
    """Lo que el alumno hizo mal; su texto es lo que ve en el resultado."""


class _Learner:
    def __init__(self):
        self._proc = None
        self._requests = self._responses = None
        self._error = None

    def _start(self, path):
        """Lanza el intermediario, que ejecuta el código del alumno en cada llamada."""
        requests_r, self._requests = os.pipe()
        self._responses, responses_w = os.pipe()
        env = {k: v for k, v in os.environ.items() if not k.startswith("QG_")}
        self._proc = subprocess.Popen(
            [sys.executable, "-u", "-P", "-m", "qgcheck.worker", path, str(requests_r), str(responses_w)],
            env=env, pass_fds=(requests_r, responses_w),
        )
        os.close(requests_r)
        os.close(responses_w)

    def _stop(self):
        for fd in (self._requests, self._responses):
            if fd is not None:
                os.close(fd)
        self._requests = self._responses = None
        if self._proc is not None:
            self._proc.kill()
            self._proc.wait()

    def _break(self, reason):
        self._error = reason
        raise LearnerError(reason)

    def _call(self, name, args, kwargs):
        if self._error is not None:
            raise LearnerError(self._error)
        try:
            send(self._requests, {"name": name, "args": encode(list(args)), "kwargs": encode(kwargs)})
            reply = receive(self._responses)
            if "error" in reply:
                raise LearnerError(str(reply["error"])[:MESSAGE_CAP])
            return decode(reply["value"])
        except LearnerError:
            raise
        except (WireError, KeyError, TypeError, ValueError, RecursionError, ImportError):
            self._break(BROKEN)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)

        def call(*args, **kwargs):
            return self._call(name, args, kwargs)

        return call


learner = _Learner()


def visible(name):
    """Marca una prueba como visible; el alumno ve `name` en lugar de un caso oculto."""

    def mark(fn):
        fn.qg_name = name
        return fn

    return mark


def counts(circuit, shots=1000, seed=7):
    """Cuentas de un circuito medido, con StatevectorSampler y semilla fija."""
    from qiskit.primitives import StatevectorSampler

    data = StatevectorSampler(seed=seed).run([circuit], shots=shots).result()[0].data
    return getattr(data, circuit.cregs[0].name).get_counts()


def aer_counts(circuit, shots=500, seed=11):
    """Como `counts`, con el Sampler de Aer, que admite `if_test` y `while_loop`."""
    from qiskit_aer.primitives import SamplerV2

    data = SamplerV2(seed=seed).run([circuit], shots=shots).result()[0].data
    return getattr(data, circuit.cregs[0].name).get_counts()
