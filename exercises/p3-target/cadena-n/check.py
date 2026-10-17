from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

from qgcheck import learner, visible

ALLOWED = {"cz", "rz", "sx", "x", "measure", "barrier"}


def ghz(n, measure=True):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    if measure:
        qc.measure_all()
    return qc


def isa(n, circuit, seed=1):
    return generate_preset_pass_manager(1, target=learner.cadena(n), seed_transpiler=seed).run(circuit)


@visible("un GHZ de 3 qubits se transpila sin SWAP")
def test_ghz3():
    out = isa(3, ghz(3))
    names = sorted(set(out.count_ops()) - {"barrier"})
    assert set(names) <= ALLOWED and "cz" in names, f"Salen las puertas {names}."


def test_ghz_up_to_6():
    for n in (4, 5, 6):
        names = sorted(set(isa(n, ghz(n)).count_ops()) - {"barrier"})
        assert set(names) <= ALLOWED and "cz" in names, f"Con n = {n} salen las puertas {names}."


def test_cz_only_between_neighbours():
    for n in (5, 7):
        target = learner.cadena(n)
        pairs = sorted(target["cz"]) if "cz" in target else []
        assert all(abs(a - b) == 1 for a, b in pairs) and len(pairs) >= n - 1, f"Con n = {n}, `cz` queda en los pares {pairs}."
