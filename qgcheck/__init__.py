"""API que usan los archivos check.py de exercises/.

    from qgcheck import learner, counts, visible

    @visible("n = 2, 3 y 4")
    def test_small():
        assert set(counts(learner.ghz(2))) == {"00", "11"}, "con n = 2 no salen solo 00 y 11"

Cada función `test_*` es un caso. Con `@visible` el alumno ve su nombre y su mensaje; sin él, el
caso es oculto: el alumno solo ve «caso oculto» y el mensaje del `assert`, así que ese mensaje no
debe revelar los datos del caso. Lo que el alumno escribió se lee con `learner.<nombre>` dentro
del caso, no al importar el archivo. Este módulo no importa qiskit hasta que se llama a un
ayudante, para que build.py pueda leer los casos sin él.
"""
from collections import Counter

from qgcheck.runner import grade  # noqa: F401


def visible(name):
    """Expone este caso con el nombre indicado."""
    def mark(fn):
        fn.qg_visible = name
        return fn
    return mark


class _Learner:
    """Accede a los nombres definidos por el código del alumno."""

    def __init__(self):
        object.__setattr__(self, "_ns", None)

    def _bind(self, ns):
        object.__setattr__(self, "_ns", ns)

    def __getattr__(self, name):
        ns = object.__getattribute__(self, "_ns")
        if ns is None:
            raise RuntimeError("learner solo existe mientras qgcheck corrige el código de un alumno")
        if name not in ns:
            raise AssertionError(f"Falta definir `{name}` en tu código.")
        return ns[name]


learner = _Learner()


def _first_register(result, what):
    data = result[0].data
    names = list(data.keys())
    if not names:
        raise AssertionError(f"{what} no mide ningún qubit: falta `measure_all()` o una medición.")
    return data[names[0]]


def counts(circuit, shots=1024, seed=7):
    """Devuelve los conteos del primer registro clásico con StatevectorSampler."""
    from qiskit.primitives import StatevectorSampler
    result = StatevectorSampler(seed=seed).run([circuit], shots=shots).result()
    return _first_register(result, "El circuito").get_counts()


def aer_counts(circuit, shots=512, seed=11):
    """Devuelve los conteos del primer registro clásico con SamplerV2."""
    from qiskit_aer.primitives import SamplerV2
    result = SamplerV2(seed=seed).run([circuit], shots=shots).result()
    return _first_register(result, "El circuito").get_counts()


def gates(circuit):
    """Cuenta operaciones por nombre, incluso dentro de bloques de control."""
    found = Counter()
    for inst in circuit.data:
        found[inst.operation.name] += 1
        for body in getattr(inst.operation, "blocks", ()):
            found.update(gates(body))
    return found


def state(circuit):
    """Devuelve el statevector del circuito sin mediciones finales."""
    from qiskit.quantum_info import Statevector
    return Statevector(circuit.remove_final_measurements(inplace=False))
