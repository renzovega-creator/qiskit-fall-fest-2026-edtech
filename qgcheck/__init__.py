"""API que usan los archivos check.py de exercises/.

    from qgcheck import learner, counts, visible

    @visible("n = 2, 3 y 4")
    def test_small():
        assert set(counts(learner.ghz(2))) == {"00", "11"}, "con n = 2 no salen solo 00 y 11"

Cada función `test_*` es un caso. Con `@visible` el alumno ve su nombre y su mensaje; sin él, el
caso es oculto: el alumno solo ve «caso oculto» y el mensaje del `assert`, así que ese mensaje no
debe revelar los datos del caso. `@hint(2)` enlaza el caso con la pista 2 del ejercicio (la primera
es la 1). Si el caso falla, el alumno ve esa pista junto a él. Lo que el alumno escribió se lee con
`learner.<nombre>` dentro del caso, no al importar el archivo. Este módulo no importa qiskit hasta
que se llama a un ayudante, para que build.py pueda leer los casos sin él.
"""
from collections import Counter

from qgcheck.runner import grade  # noqa: F401


def visible(name):
    """Expone este caso con el nombre indicado."""
    def mark(fn):
        fn.qg_visible = name
        return fn
    return mark


def hint(number):
    """Enlaza este caso con la pista `number` (desde 1) de `hints` del ejercicio."""
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError(f"la pista se numera desde 1, no {number!r}")

    def mark(fn):
        fn.qg_hint = number
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


def unsupported(circuit, target):
    """Lista las instrucciones del circuito que el target no admite donde están: ['h en 0', 'cz en 0-2']."""
    found = []
    for inst in circuit.data:
        at = tuple(circuit.find_bit(q).index for q in inst.qubits)
        if not target.instruction_supported(inst.operation.name, at):
            found.append(f"{inst.operation.name} en {'-'.join(map(str, at))}")
    return found


def operator(circuit):
    """Devuelve el operador de un circuito sobre los qubits virtuales del circuito original.

    Si el circuito está transpilado, aplica el layout inicial y el final para que se pueda comparar
    con el operador del original. Solo construye la matriz de los qubits que el circuito toca, así
    que sirve con un circuito transpilado a un chip de 156 qubits.
    """
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator

    body = circuit.remove_final_measurements(inplace=False)
    layout = body.layout
    if layout is None:
        return Operator(body)
    first, last = layout.initial_index_layout(filter_ancillas=True), layout.final_index_layout()
    touched = {body.find_bit(q).index for inst in body.data for q in inst.qubits}
    used = sorted(touched | set(first) | set(last))
    at = {physical: k for k, physical in enumerate(used)}
    small = QuantumCircuit(len(used))
    for inst in body.data:
        small.append(inst.operation, [at[body.find_bit(q).index] for q in inst.qubits])
    n = len(first)

    def index(places, x):
        return sum(((x >> v) & 1) << at[places[v]] for v in range(n))

    full = Operator(small).data
    rows = [index(last, y) for y in range(2**n)]
    cols = [index(first, x) for x in range(2**n)]
    return Operator(full[np.ix_(rows, cols)])
