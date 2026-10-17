from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import learner, visible

CHIP = CouplingMap([[0, 1], [1, 2], [1, 3], [3, 4]])
CHIP.make_symmetric()


def star():
    qc = QuantumCircuit(4)
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.cx(0, 3)
    return qc


def swaps(layout, nivel=0, seed=1):
    pm = generate_preset_pass_manager(nivel, coupling_map=CHIP, initial_layout=layout, seed_transpiler=seed)
    return pm.run(star()).count_ops().get("swap", 0)


@visible("el routing no inserta ningún SWAP")
def test_no_swap():
    layout = list(learner.layout_inicial)
    n = swaps(layout)
    assert n == 0, f"Con el layout {layout} el routing inserta {n} swap. ¿Qué qubit físico tiene tres vecinos?"


def test_other_seeds():
    layout = list(learner.layout_inicial)
    for seed in (2, 3, 4):
        n = swaps(layout, seed=seed)
        assert n == 0, f"Con seed = {seed} y el layout {layout} el routing inserta {n} swap."


def test_higher_levels_keep_the_layout():
    layout = list(learner.layout_inicial)
    for nivel in (1, 2, 3):
        n = swaps(layout, nivel=nivel)
        assert n == 0, f"Con nivel = {nivel} y el layout {layout} el routing inserta {n} swap."
