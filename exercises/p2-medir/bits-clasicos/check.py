from qiskit import QuantumCircuit

from qgcheck import learner, visible


def lesson_circuit():
    qc = QuantumCircuit(3, 1)
    qc.x([0, 2])
    qc.measure_all()
    return qc


def placed(qc):
    return [(inst.operation.name, [qc.find_bit(q).index for q in inst.qubits]) for inst in qc.data]


@visible("tu apuesta es el número de bits clásicos de qc")
def test_bet():
    assert learner.prediccion == learner.qc.num_clbits, (
        "Tu apuesta no coincide con `qc.num_clbits`. Recuerda: `measure_all` no reutiliza el registro `c` que ya existía.")


def test_same_circuit():
    qc = learner.qc
    assert qc == lesson_circuit(), (
        f"`qc` tiene ahora {qc.num_qubits} qubits, {qc.num_clbits} bits clásicos y las operaciones {placed(qc)}; "
        "el circuito de la lección cambió.")
