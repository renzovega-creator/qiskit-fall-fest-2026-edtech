from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import learner, visible

GRID = CouplingMap.from_grid(3, 3)


def transpile_with(qc, seed):
    return generate_preset_pass_manager(1, coupling_map=GRID, basis_gates=["cx", "rz", "sx", "x"], seed_transpiler=seed).run(qc)


def cx(circuit):
    """Las cx del circuito, o None si lo que devolvió el alumno no es un circuito."""
    return circuit.count_ops().get("cx", 0) if isinstance(circuit, QuantumCircuit) else None


def cx_per_seed(qc, seeds):
    return [cx(transpile_with(qc, seed)) for seed in seeds]


@visible("devuelve un circuito transpilado")
def test_returns_a_circuit():
    chosen = learner.mejor_de(random_circuit(9, 6, max_operands=2, seed=7), range(10))
    assert isinstance(chosen, QuantumCircuit), f"`mejor_de` devuelve {type(chosen).__name__}; debe devolver un `QuantumCircuit`."


@visible("el circuito elegido tiene el mínimo de cx de las diez semillas")
def test_best_of_ten():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    got = cx(learner.mejor_de(qc, range(10)))
    assert got == min(cx_per_seed(qc, range(10))), f"Con semillas = range(10), el circuito elegido tiene {got} cx."


def test_other_circuit():
    qc = random_circuit(9, 6, max_operands=2, seed=3)
    got = cx(learner.mejor_de(qc, range(10)))
    assert got == min(cx_per_seed(qc, range(10))), f"Con otro circuito, el elegido por `mejor_de` tiene {got} cx."


def test_only_the_given_seeds():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    seeds = [3, 0, 1]
    got = cx(learner.mejor_de(qc, seeds))
    assert got == min(cx_per_seed(qc, seeds)), f"Con semillas = {seeds}, el circuito elegido tiene {got} cx."


def test_accepts_a_generator():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    got = cx(learner.mejor_de(qc, (s for s in range(6))))
    assert got == min(cx_per_seed(qc, range(6))), f"Con semillas = un generador de 0 a 5, el elegido tiene {got} cx."
