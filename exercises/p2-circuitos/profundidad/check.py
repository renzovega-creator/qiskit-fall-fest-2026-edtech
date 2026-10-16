from qiskit import QuantumCircuit

from qgcheck import learner, visible


def lesson_circuit():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.x(1)
    qc.cx(0, 1)
    qc.z(2)
    qc.h(1)
    return qc


@visible("tu apuesta es la profundidad de qc")
def test_bet():
    assert learner.prediccion == learner.qc.depth(), (
        "Tu apuesta no coincide con `qc.depth()`. Una puerta espera a que sus qubits queden libres: cuenta las capas.")


def test_same_circuit():
    qc = learner.qc
    assert qc == lesson_circuit(), (
        f"`qc` tiene ahora {qc.num_qubits} qubits y las puertas {dict(qc.count_ops())}; el circuito de la lección cambió.")
