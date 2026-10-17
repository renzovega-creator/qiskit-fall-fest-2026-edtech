from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford, random_clifford
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import HighLevelSynthesis
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig

from qgcheck import learner, visible


def synthesize(cl, methods):
    qc = QuantumCircuit(cl.num_qubits)
    qc.append(cl, range(cl.num_qubits))
    return PassManager([HighLevelSynthesis(hls_config=HLSConfig(clifford=methods))]).run(qc)


def outcome(circuit, cl):
    """Describe el resultado sin mostrar el Clifford: sintetizado y equivalente, sintetizado y distinto, o intacto."""
    if "clifford" in circuit.count_ops():
        return "intacto"
    return "sintetizado" if Clifford(circuit) == cl else "distinto"


@visible("un Clifford de 3 qubits se sintetiza y es equivalente")
def test_small():
    cl = random_clifford(3, seed=1)
    got = outcome(synthesize(cl, [(learner.MiClifford(), {})]), cl)
    assert got == "sintetizado", f"El resultado queda {got}."


@visible("uno de 5 qubits queda intacto")
def test_big():
    cl = random_clifford(5, seed=1)
    got = outcome(synthesize(cl, [(learner.MiClifford(), {})]), cl)
    assert got == "intacto", f"El resultado queda {got}."


def test_other_small():
    for n, seed in ((2, 2), (3, 3), (2, 4)):
        cl = random_clifford(n, seed=seed)
        got = outcome(synthesize(cl, [(learner.MiClifford(), {})]), cl)
        assert got == "sintetizado", f"Con n = {n} y seed = {seed} el resultado queda {got}."


def test_four_qubits_untouched():
    cl = random_clifford(4, seed=2)
    got = outcome(synthesize(cl, [(learner.MiClifford(), {})]), cl)
    assert got == "intacto", f"Con n = 4 el resultado queda {got}."


def test_fallback_takes_over():
    for n in (4, 5, 6):
        cl = random_clifford(n, seed=5)
        got = outcome(synthesize(cl, [(learner.MiClifford(), {}), "greedy"]), cl)
        assert got == "sintetizado", f"Con n = {n} y respaldo `greedy` el resultado queda {got}."
