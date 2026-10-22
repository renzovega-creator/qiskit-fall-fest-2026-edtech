from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator

from qgcheck import inside, learner, operator, visible


@inside
def isa(circuit, seed=1):
    return transpile(circuit, learner.MiBackend(), seed_transpiler=seed)


def ghz(order):
    qc = QuantumCircuit(3)
    qc.h(order[0])
    qc.cx(order[0], order[1])
    qc.cx(order[1], order[2])
    return qc


@visible("una CX entre los extremos no necesita SWAP")
def test_far_cx():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 2)
    ops = sorted(isa(qc).count_ops())
    assert ops == ["cz", "rz", "sx"], f"Salen las puertas {ops}."


@visible("un GHZ de 3 qubits cabe en la cadena sin SWAP")
def test_ghz_fits():
    ops = sorted(isa(ghz((0, 1, 2))).count_ops())
    assert "swap" not in ops and "cz" in ops, f"Salen las puertas {ops}."


@inside
def cz_pairs():
    return sorted(learner.MiBackend().target["cz"])


def test_chain_pairs_only():
    pairs = cz_pairs()
    assert all(abs(a - b) == 1 for a, b in pairs) and len(pairs) >= 2, f"`MiBackend` admite cz en los pares {pairs}."


def test_other_orders():
    for order in ((2, 1, 0), (1, 0, 2), (1, 2, 0)):
        qc = ghz(order)
        out = isa(qc, 3)
        names = sorted(set(out.count_ops()))
        assert set(names) <= {"cz", "rz", "sx", "x"}, f"Con orden = {order} salen las puertas {names}."
        assert operator(out).equiv(Operator(qc)), f"Con orden = {order} el circuito transpilado cambia de operador."
