from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import learner, visible

GRID = CouplingMap.from_grid(3, 3)


def cx_count(circuit, seed):
    pm = generate_preset_pass_manager(
        2, coupling_map=GRID, basis_gates=["cx", "rz", "sx", "x"],
        routing_method=learner.metodo, seed_transpiler=seed)
    return pm.run(circuit).count_ops().get("cx", 0)


@visible("55 CNOT o menos")
def test_55_cx():
    got = cx_count(random_circuit(9, 6, max_operands=2, seed=3), 0)
    assert got <= 55, f"Con metodo = {learner.metodo!r} salen {got} CNOT."


def test_other_seeds():
    for seed in (1, 2):
        got = cx_count(random_circuit(9, 6, max_operands=2, seed=3), seed)
        assert got <= 55, f"Con seed = {seed} y metodo = {learner.metodo!r} salen {got} CNOT."


def test_deeper_circuit():
    got = cx_count(random_circuit(9, 8, max_operands=2, seed=7), 0)
    assert got <= 60, f"Con un circuito de 8 capas y metodo = {learner.metodo!r} salen {got} CNOT."
