from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager

from qgcheck import inside, learner, visible


@inside
def counted(circuit):
    pm = PassManager([learner.ContarDosQubits()])
    out = pm.run(circuit)
    return pm.property_set.get("n2q"), out


def mixed():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cz(1, 2)
    qc.swap(0, 2)
    return qc


@visible("cuenta las puertas de dos qubits")
def test_counts():
    got, _ = counted(mixed())
    assert got == 3, f"Escribe n2q = {got}."


@visible("no cambia el circuito")
def test_dag_untouched():
    qc = mixed()
    _, out = counted(qc)
    assert out == qc, f"El circuito sale con las puertas {dict(out.count_ops())}."


def test_none():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.x(1)
    got, _ = counted(qc)
    assert got is not None and got == 0, f"Sin puertas de dos qubits escribe n2q = {got}."


def test_toffoli():
    qc = QuantumCircuit(3)
    qc.ccx(0, 1, 2)
    qc.cx(0, 1)
    got, _ = counted(qc)
    assert got == 1, f"Con una Toffoli y una CX escribe n2q = {got}."


def test_more_gates():
    for n in (4, 6):
        qc = QuantumCircuit(n)
        for k in range(n - 1):
            qc.cx(k, k + 1)
        qc.measure_all()
        got, _ = counted(qc)
        assert got == n - 1, f"Con n = {n} escribe n2q = {got}."
