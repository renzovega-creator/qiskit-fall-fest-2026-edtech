from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import inside, learner, visible

GRID = CouplingMap.from_grid(3, 3)


def transpile_with(qc, seed):
    return generate_preset_pass_manager(1, coupling_map=GRID, basis_gates=["cx", "rz", "sx", "x"], seed_transpiler=seed).run(qc)


@inside
def chosen(qc, seeds, kind="list"):
    """Devuelve el circuito de `mejor_de` o el tipo de su resultado.

    `kind` da la forma de las semillas: `list`, `range` (`seeds` son los argumentos de `range`) o
    `generator`.
    """
    given = {"list": list, "range": lambda s: range(*s), "generator": lambda s: (k for k in s)}[
        kind
    ](seeds)
    out = learner.mejor_de(qc, given)
    return (out, None) if isinstance(out, QuantumCircuit) else (None, type(out).__name__)


def chosen_cx(qc, seeds, kind="list"):
    """Devuelve las `cx` del circuito elegido, o `None` si no devolvió un circuito."""
    circuit, _ = chosen(qc, seeds, kind)
    return None if circuit is None else cx(circuit)


def cx(circuit):
    return circuit.count_ops().get("cx", 0)


def cx_per_seed(qc, seeds):
    return [cx(transpile_with(qc, seed)) for seed in seeds]


@visible("devuelve un circuito transpilado")
def test_returns_a_circuit():
    circuit, other = chosen(random_circuit(9, 6, max_operands=2, seed=7), [0, 10], "range")
    assert circuit is not None, f"`mejor_de` devuelve {other}; debe devolver un `QuantumCircuit`."


@visible("el circuito elegido tiene el mínimo de cx de las diez semillas")
def test_best_of_ten():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    got = chosen_cx(qc, [0, 10], "range")
    assert got == min(cx_per_seed(qc, range(10))), f"Con semillas = range(10), el circuito elegido tiene {got} cx."


def test_other_circuit():
    qc = random_circuit(9, 6, max_operands=2, seed=3)
    got = chosen_cx(qc, [0, 10], "range")
    assert got == min(cx_per_seed(qc, range(10))), f"Con otro circuito, el elegido por `mejor_de` tiene {got} cx."


def test_only_the_given_seeds():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    seeds = [3, 0, 1]
    got = chosen_cx(qc, seeds)
    assert got == min(cx_per_seed(qc, seeds)), f"Con semillas = {seeds}, el circuito elegido tiene {got} cx."


def test_accepts_a_generator():
    qc = random_circuit(9, 6, max_operands=2, seed=7)
    got = chosen_cx(qc, list(range(6)), "generator")
    assert got == min(cx_per_seed(qc, range(6))), f"Con semillas = un generador de 0 a 5, el elegido tiene {got} cx."
