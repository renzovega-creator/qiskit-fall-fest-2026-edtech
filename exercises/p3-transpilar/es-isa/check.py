from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, visible

BACKEND = FakeFez()
TARGET = BACKEND.target
EDGES = set(TARGET.build_coupling_map().get_edges())
A, B = sorted(EDGES)[0]
FAR = next(k for k in range(TARGET.num_qubits) if k != A and (A, k) not in EDGES and (k, A) not in EDGES)


def toffoli():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.ccx(0, 1, 2)
    return qc


def verdict(circuit):
    return "acepta" if learner.es_isa(circuit, TARGET) else "rechaza"


@visible("acepta un circuito transpilado para FakeFez")
def test_accepts_transpiled():
    isa = generate_preset_pass_manager(1, backend=BACKEND, seed_transpiler=1).run(toffoli())
    answer = verdict(isa)
    assert answer == "acepta", f"Tu `es_isa` {answer} el circuito que salió del transpilador."


@visible("rechaza el circuito original, con h y ccx")
def test_rejects_original():
    answer = verdict(toffoli())
    assert answer == "rechaza", f"Tu `es_isa` {answer} un circuito con `h` y `ccx`."


def test_neighbours_and_far_pairs():
    near, far = QuantumCircuit(TARGET.num_qubits), QuantumCircuit(TARGET.num_qubits)
    near.cz(A, B)
    far.cz(A, FAR)
    for name, circuit, want in (("neighbours", near, "acepta"), ("far", far, "rechaza")):
        answer = verdict(circuit)
        assert answer == want, f"Con una `cz` entre qubits = {name}, tu `es_isa` {answer} el circuito."


def test_gate_outside_the_target():
    circuit = QuantumCircuit(TARGET.num_qubits)
    circuit.h(A)
    answer = verdict(circuit)
    assert answer == "rechaza", f"Con una `h` suelta, tu `es_isa` {answer} el circuito."


def test_measurement_is_supported():
    circuit = QuantumCircuit(TARGET.num_qubits, 1)
    circuit.sx(A)
    circuit.measure(A, 0)
    answer = verdict(circuit)
    assert answer == "acepta", f"Con una `sx` y una medición, tu `es_isa` {answer} el circuito."
