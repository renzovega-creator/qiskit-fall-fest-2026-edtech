from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import random_unitary
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

from qgcheck import learner, visible

BACKEND = FakeSherbrooke()


def unitary_and_swap(seed):
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(random_unitary(4, seed=seed)), range(2))
    qc.swap(0, 1)
    return qc


def reference(circuit):
    return [generate_preset_pass_manager(nivel, backend=BACKEND, seed_transpiler=12345).run(circuit).count_ops().get("ecr", 0)
            for nivel in range(4)]


@visible("devuelve una cuenta por cada nivel, de 0 a 3")
def test_four_counts():
    got = list(learner.ecr_por_nivel(unitary_and_swap(12345)))
    assert len(got) == 4, f"`ecr_por_nivel` devuelve {got}: debe tener una cuenta por nivel."


@visible("los niveles altos fusionan la unitaria y el SWAP")
def test_levels_2_and_3_merge():
    got = list(learner.ecr_por_nivel(unitary_and_swap(12345)))
    assert len(got) == 4 and got[3] < got[0], f"`ecr_por_nivel` devuelve {got}: el nivel 3 debería usar menos ecr que el 0."


def test_other_unitaries():
    for seed in (7, 99):
        got = list(learner.ecr_por_nivel(unitary_and_swap(seed)))
        assert got == reference(unitary_and_swap(seed)), f"Con la unitaria de seed = {seed}, `ecr_por_nivel` devuelve {got}."


def test_counts_the_two_qubit_gate_of_the_chip():
    qc = unitary_and_swap(5)
    got = list(learner.ecr_por_nivel(qc))
    assert got == reference(qc) and all(isinstance(n, int) for n in got), f"Con la unitaria de seed = 5, `ecr_por_nivel` devuelve {got}."
