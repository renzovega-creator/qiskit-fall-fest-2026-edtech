from qiskit import QuantumCircuit

from qgcheck import counts, learner, visible


def lesson_circuit():
    qc = QuantumCircuit(3)
    qc.x([0, 2])
    qc.measure_all()
    return qc


def placed(qc):
    return [(inst.operation.name, [qc.find_bit(q).index for q in inst.qubits]) for inst in qc.data]


@visible("tu apuesta es la cadena que mide Qiskit")
def test_bet():
    got = sorted(counts(learner.circuito))
    assert got == [learner.prediccion], (
        "Tu apuesta no coincide con la cadena medida. Escribe primero el bit del qubit 2 y al final el del qubit 0.")


def test_same_circuit():
    qc = learner.circuito
    assert qc == lesson_circuit(), (
        f"`circuito` tiene ahora {qc.num_qubits} qubits y las operaciones {placed(qc)}; el circuito de la lección cambió.")
