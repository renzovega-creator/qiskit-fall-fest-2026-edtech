import functools

from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, visible

BACKEND = FakeFez()


def step(n):
    qc = QuantumCircuit(n)
    for i in range(n - 1):
        qc.rzz(0.2, i, i + 1)
    for i in range(n):
        qc.rx(0.1, i)
    return qc


@functools.cache
def depths(n):
    """Profundidad transpilada (nivel 3, FakeFez, seed_transpiler=1) de 1 a 10 pasos."""
    pm = generate_preset_pass_manager(3, backend=BACKEND, seed_transpiler=1)
    out = {}
    for pasos in range(1, 11):
        qc = QuantumCircuit(n)
        for _ in range(pasos):
            qc.compose(step(n), inplace=True)
        out[pasos] = pm.run(qc).depth()
    return out


def fits(n, budget):
    return max([p for p, d in depths(n).items() if d <= budget], default=0)


@visible("con 6 espines y un presupuesto de 150 caben tantos pasos como indica la profundidad transpilada")
def test_budget():
    got = learner.pasos_max(6, 150)
    assert got == fits(6, 150), f"Con n = 6 y presupuesto = 150, `pasos_max` devuelve {got}; esperaba {fits(6, 150)}."


@visible("si ni un paso cabe, devuelve 0")
def test_nothing_fits():
    got = learner.pasos_max(6, 5)
    assert got == 0, f"Con n = 6 y presupuesto = 5, `pasos_max` devuelve {got}; ni un paso cabe."


def test_everything_fits():
    got = learner.pasos_max(4, 100000)
    assert got == 10, f"Con n = 4 y presupuesto = 100000, `pasos_max` devuelve {got}."


def test_equal_depth_fits():
    budget = depths(4)[5]
    got = learner.pasos_max(4, budget)
    assert got == fits(4, budget), f"Con n = 4 y presupuesto = {budget}, `pasos_max` devuelve {got}."


def test_other_size():
    budget = depths(3)[7] + 1
    got = learner.pasos_max(3, budget)
    assert got == fits(3, budget), f"Con n = 3 y presupuesto = {budget}, `pasos_max` devuelve {got}."
