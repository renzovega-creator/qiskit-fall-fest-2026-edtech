from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.quantum_info import Operator
from qiskit.transpiler import generate_preset_pass_manager

from qgcheck import inside, learner, visible

BACKEND = GenericBackendV2(5, seed=1)


@inside
def with_dd(circuit):
    return learner.dd_pm.run(circuit)


def scheduled(n, seed):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, range(1, n))
    return generate_preset_pass_manager(1, backend=BACKEND, scheduling_method="asap", seed_transpiler=seed).run(qc)


def x_count(circuit):
    return circuit.count_ops().get("x", 0)


@visible("el pass manager añade puertas X en las esperas")
def test_adds_x():
    before = scheduled(5, 1234)
    after = with_dd(before)
    assert x_count(after) > x_count(before), f"Había {x_count(before)} x y ahora hay {x_count(after)}."


@visible("el operador no cambia")
def test_operator():
    before = scheduled(5, 1234)
    after = with_dd(before)
    assert Operator(after).equiv(Operator(before)), "El circuito con DD tiene otro operador."


def test_only_x_pairs():
    before = scheduled(5, 1234)
    after = with_dd(before)
    added = x_count(after) - x_count(before)
    assert added > 0 and added % 2 == 0 and after.count_ops().get("y", 0) == 0, f"Con `dd_pm`, añadió {added} x y {after.count_ops().get('y', 0)} y."


def test_other_circuit():
    for n, seed in ((4, 7), (3, 11)):
        before = scheduled(n, seed)
        after = with_dd(before)
        assert x_count(after) > x_count(before) and Operator(after).equiv(Operator(before)), (
            f"Con n = {n} y seed = {seed} hay {x_count(after)} x y el operador "
            f"{'se conserva' if Operator(after).equiv(Operator(before)) else 'cambia'}."
        )
