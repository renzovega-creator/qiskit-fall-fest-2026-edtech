import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator

from qgcheck import learner, visible


def value(circuit, observable):
    return float(StatevectorEstimator().run([(circuit, observable)]).result()[0].data.evs)


def all_up(n):
    return QuantumCircuit(n)


def one_flipped(n):
    qc = QuantumCircuit(n)
    qc.x(0)
    return qc


def all_plus(n):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    return qc


@visible("M_Z vale 1 con todos los espines en |0⟩ y 0,5 con uno volteado")
def test_z_axis():
    op = learner.magnetizacion(4)
    assert op.num_qubits == 4 and len(op) == 4, "Para n = 4 el observable debe ser una suma de 4 términos de un solo qubit."
    up, flipped = value(all_up(4), op), value(one_flipped(4), op)
    assert np.isclose(up, 1) and np.isclose(flipped, 0.5), f"M_Z vale {up:.2f} con todos en |0⟩ y {flipped:.2f} con uno volteado; esperaba 1 y 0,5."


@visible("M_X vale 1 con todos en |+⟩ y M_Z vale 0")
def test_x_axis():
    plus = all_plus(4)
    mx, mz = value(plus, learner.magnetizacion(4, "X")), value(plus, learner.magnetizacion(4, "Z"))
    assert np.isclose(mx, 1) and np.isclose(mz, 0), f"En |+⟩⁴, M_X vale {mx:.2f} y M_Z vale {mz:.2f}; esperaba 1 y 0."


def test_other_sizes():
    for n in (1, 3, 6):
        op = learner.magnetizacion(n)
        assert op.num_qubits == n, f"Con n = {n} el observable tiene {op.num_qubits} qubits."
        up, flipped = value(all_up(n), op), value(one_flipped(n), op)
        assert np.isclose(up, 1) and np.isclose(flipped, 1 - 2 / n), (
            f"Con n = {n}, el observable vale {round(up, 2)} con todos en |0⟩ y {round(flipped, 2)} con el primer espín volteado.")


def test_default_axis_is_z():
    got = value(one_flipped(4), learner.magnetizacion(4))
    assert np.isclose(got, 0.5), f"Sin indicar el eje y con n = 4, el observable vale {round(got, 2)} con el primer espín volteado."
