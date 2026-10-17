from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, grover_operator

from qgcheck import learner, visible


def grover(marked):
    qc = QuantumCircuit(3)
    qc.h([0, 1, 2])
    flags = [1] * 8
    flags[marked] = -1
    return qc.compose(grover_operator(DiagonalGate(flags)))


@visible("la fidelidad está entre 0 y 1")
def test_in_range():
    f = learner.fidelidad(grover(7), 1)
    assert isinstance(f, float) and 0 < f <= 1, f"`fidelidad` devuelve {f}: debe ser un número entre 0 y 1."


@visible("el nivel 3 se acerca a la distribución ideal")
def test_level_3_close():
    f = learner.fidelidad(grover(7), 3)
    assert f > 0.97, f"Con nivel = 3, `fidelidad` devuelve {f:.3f}."


def test_level_0_is_noisier():
    f = learner.fidelidad(grover(2), 0)
    assert 0.85 < f < 0.97, f"Con el estado marcado 2 y nivel = 0, `fidelidad` devuelve {round(f, 3)}."
