from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from qgcheck import inside, learner, visible

IONS = {"rx", "ry", "rxx"}


@inside
def translated(circuit):
    return learner.traducir.run(circuit)


def hcx():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 0)
    return qc


def three_qubits():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cz(1, 2)
    qc.swap(0, 2)
    qc.s(1)
    return qc


def hcz():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.h(1)
    qc.cz(0, 1)
    qc.ry(0.4, 1)
    return qc


@visible("solo quedan rx, ry y rxx")
def test_gate_set():
    names = sorted(translated(hcx()).count_ops())
    assert set(names) <= IONS and "rxx" in names, f"Quedan las puertas {names}."


@visible("el operador no cambia")
def test_operator():
    out = translated(hcx())
    assert Operator(out).equiv(Operator(hcx())), "El circuito traducido tiene otro operador."


def test_three_qubits():
    qc = three_qubits()
    out = translated(qc)
    names = sorted(out.count_ops())
    assert set(names) <= IONS, f"Con circuito = tres_qubits quedan las puertas {names}."
    assert Operator(out).equiv(Operator(qc)), "Con circuito = tres_qubits cambia el operador."


def test_other_circuit():
    qc = hcz()
    out = translated(qc)
    names = sorted(out.count_ops())
    assert set(names) <= IONS, f"Con circuito = hcz quedan las puertas {names}."
    assert Operator(out).equiv(Operator(qc)), "Con circuito = hcz cambia el operador."
