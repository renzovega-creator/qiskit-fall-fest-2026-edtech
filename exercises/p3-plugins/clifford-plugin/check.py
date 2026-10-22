from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford, random_clifford
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import HighLevelSynthesis
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig

from qgcheck import inside, learner, visible


@inside
def synthesized(cl_circuit, fallback):
    """Pasa el circuito con un Clifford por `HighLevelSynthesis` con `MiClifford` (y `greedy` de
    respaldo si `fallback`). Devuelve None si el Clifford queda intacto."""
    methods = [(learner.MiClifford(), {}), "greedy"] if fallback else [(learner.MiClifford(), {})]
    circuit = PassManager([HighLevelSynthesis(hls_config=HLSConfig(clifford=methods))]).run(
        cl_circuit
    )
    return None if "clifford" in circuit.count_ops() else circuit


def outcome(n, seed, fallback=False):
    """Describe el resultado sin mostrar el Clifford: sintetizado y equivalente, sintetizado y distinto, o intacto."""
    cl = random_clifford(n, seed=seed)
    qc = QuantumCircuit(n)
    qc.append(cl, range(n))
    circuit = synthesized(qc, fallback)
    if circuit is None:
        return "intacto"
    return "sintetizado" if Clifford(circuit) == cl else "distinto"


@visible("un Clifford de 3 qubits se sintetiza y es equivalente")
def test_small():
    got = outcome(3, 1)
    assert got == "sintetizado", f"El resultado queda {got}."


@visible("uno de 5 qubits queda intacto")
def test_big():
    got = outcome(5, 1)
    assert got == "intacto", f"El resultado queda {got}."


def test_other_small():
    for n, seed in ((2, 2), (3, 3), (2, 4)):
        got = outcome(n, seed)
        assert got == "sintetizado", f"Con n = {n} y seed = {seed} el resultado queda {got}."


def test_four_qubits_untouched():
    got = outcome(4, 2)
    assert got == "intacto", f"Con n = 4 el resultado queda {got}."


def test_fallback_takes_over():
    for n in (4, 5, 6):
        got = outcome(n, 5, fallback=True)
        assert got == "sintetizado", f"Con n = {n} y respaldo `greedy` el resultado queda {got}."
