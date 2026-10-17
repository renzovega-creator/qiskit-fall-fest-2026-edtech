from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

from qgcheck import learner, visible


def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


def ghz4():
    qc = QuantumCircuit(4)
    qc.h(0)
    for k in range(3):
        qc.cx(k, k + 1)
    return qc


def used_pairs(isa):
    return sorted({tuple(sorted(isa.find_bit(q).index for q in inst.qubits)) for inst in isa.data if inst.operation.num_qubits == 2})


def run(circuit, seed, level=3):
    return generate_preset_pass_manager(level, target=learner.anillo, seed_transpiler=seed).run(circuit)


@visible("el transpilador nunca usa el par (1, 2)")
def test_avoids_pair():
    pairs = used_pairs(run(bell(), 1))
    assert pairs and (1, 2) not in pairs, f"Con el nivel 3 usa los pares {pairs}."


def test_other_seeds_and_levels():
    for seed, level in ((2, 3), (3, 1), (4, 2)):
        pairs = used_pairs(run(ghz4(), seed, level))
        assert (1, 2) not in pairs, f"Con seed = {seed} y nivel = {level} usa los pares {pairs}."


def test_rest_of_the_ring_stays():
    pairs = sorted(learner.anillo["cz"])
    assert {(0, 1), (2, 3), (3, 0)} <= set(pairs), f"El `anillo` solo admite cz en los pares {pairs}."
