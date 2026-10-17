from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, visible

FEZ = FakeFez()


def ops(pm, circuit):
    return dict(pm.run(circuit).count_ops())


def plain(circuit):
    return ops(generate_preset_pass_manager(0, backend=FEZ, seed_transpiler=1), circuit)


def build(with_s, with_h):
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    if with_s:
        qc.s(1)
        qc.sdg(1)
    if with_h:
        qc.h(2)
        qc.h(2)
    qc.cx(1, 2)
    return qc


def stripped():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    return qc


@visible("el circuito con pares da lo mismo que el que no los tiene")
def test_pairs_cancel():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.s(0)
    qc.sdg(0)
    qc.cx(0, 1)
    qc.h(1)
    qc.h(1)
    qc.x(1)
    ref = QuantumCircuit(2)
    ref.h(0)
    ref.cx(0, 1)
    ref.x(1)
    got = ops(learner.pm_nivel0, qc)
    assert got == plain(ref), f"Salen las puertas {got}."


def test_s_pairs_only():
    got = ops(learner.pm_nivel0, build(True, False))
    assert got == plain(stripped()), f"Con pares = «S, S†» salen las puertas {got}."


def test_h_pairs_only():
    got = ops(learner.pm_nivel0, build(False, True))
    assert got == plain(stripped()), f"Con pares = «H, H» salen las puertas {got}."
