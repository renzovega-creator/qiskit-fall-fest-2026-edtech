from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.transpiler import PassManager

from qgcheck import learner, visible


def with_swaps(pairs, n=3):
    qc = QuantumCircuit(n)
    qc.h(0)
    for a, b in pairs:
        qc.swap(a, b)
        qc.cx(b, (b + 1) % n)
    return qc


def run(circuit):
    return PassManager([learner.SwapACx()]).run(circuit)


@visible("ningún swap y el mismo operador")
def test_no_swap():
    qc = with_swaps([(0, 1), (1, 2)])
    out = run(qc)
    ops = dict(out.count_ops())
    assert "swap" not in ops and Operator(out).equiv(Operator(qc)), f"Salen las puertas {ops}."


@visible("cada swap se convierte en tres cx")
def test_three_cx_each():
    qc = with_swaps([(0, 1), (1, 2)])
    ops = dict(run(qc).count_ops())
    assert ops.get("cx", 0) == 8, f"Salen {ops.get('cx', 0)} cx."


def test_reversed_arguments():
    for pairs in (((2, 0),), ((1, 0), (2, 1))):
        qc = with_swaps(pairs)
        out = run(qc)
        ops = dict(out.count_ops())
        assert "swap" not in ops and Operator(out).equiv(Operator(qc)), f"Con pares = {pairs} salen las puertas {ops}."


def test_without_swaps_unchanged():
    qc = QuantumCircuit(3)
    qc.cx(0, 1)
    qc.cz(1, 2)
    out = run(qc)
    assert out == qc, f"Con pares = () el circuito cambia: {dict(out.count_ops())}."


def test_wider_circuit():
    qc = with_swaps([(0, 3), (1, 4), (3, 4)], n=5)
    out = run(qc)
    ops = dict(out.count_ops())
    assert "swap" not in ops and Operator(out).equiv(Operator(qc)), f"Con n = 5 salen las puertas {ops}."
