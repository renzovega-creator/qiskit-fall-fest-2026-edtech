from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator

from qgcheck import learner, visible


def expected(circuit):
    qc = QuantumCircuit(circuit.num_qubits)
    qc.ccx(0, 1, 2)
    qc.compose(circuit, inplace=True)
    qc.h(0)
    return qc


def toffoli_at(circuit):
    """Los índices de los qubits de la primera Toffoli del circuito."""
    return next(([circuit.find_bit(q).index for q in inst.qubits] for inst in circuit.data if inst.operation.name == "ccx"), None)


def unitary_circuit(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, 1)
    qc.t(1)
    qc.cx(1, 2)
    return qc


@visible("la H va al final y la Toffoli al principio")
def test_front_and_back():
    qc = unitary_circuit(3)
    out = learner.envolver(qc)
    assert Operator(out).equiv(Operator(expected(qc))), "El operador del resultado no es Toffoli, el circuito y H, en ese orden."


@visible("el resultado conserva la medición y el bloque if")
def test_keeps_the_rest():
    q = QuantumRegister(3, "q")
    c = ClassicalRegister(3, "c")
    qc = QuantumCircuit(q, c)
    qc.h(q[0])
    qc.measure(q[0], c[0])
    with qc.if_test((c, 1)):
        qc.rz(0.5, q[1])
    out = learner.envolver(qc)
    ops = dict(out.count_ops())
    assert ops.get("ccx") == 1 and ops.get("h") == 2 and ops.get("measure") == 1 and ops.get("if_else") == 1, f"Las operaciones del resultado son {ops}."


def test_wider_circuit():
    for n in (4, 5):
        qc = unitary_circuit(3)
        wide = QuantumCircuit(n)
        wide.compose(qc, [0, 1, 2], inplace=True)
        wide.cx(2, n - 1)
        out = learner.envolver(wide)
        assert Operator(out).equiv(Operator(expected(wide))), (
            f"Con n = {n} la Toffoli del resultado actúa en los qubits {toffoli_at(out)} y el operador no es el esperado.")
