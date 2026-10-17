from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import learner, visible

CHIP = GenericBackendV2(15, coupling_map=CouplingMap.from_line(15), seed=1)


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, range(1, n))
    return qc


def reference(n, nivel):
    return generate_preset_pass_manager(nivel, backend=CHIP, seed_transpiler=1234).run(ghz(n)).count_ops().get("cx", 0)


@visible("el routing añade CNOT a las 14 del original")
def test_routing_adds_cx():
    got = learner.cx_transpilado(ghz(15), 0)
    assert got > 14, f"Con nivel = 0 salen {got} cx; los SWAP del routing deberían añadir más que las 14 originales."


@visible("el nivel 3 usa menos CNOT que el nivel 0")
def test_level_3_is_cheaper():
    low, high = learner.cx_transpilado(ghz(15), 0), learner.cx_transpilado(ghz(15), 3)
    assert high < low, f"El nivel 3 deja {high} cx y el nivel 0 deja {low}."


def test_other_sizes_and_levels():
    for n in (8, 10):
        for nivel in range(4):
            got = learner.cx_transpilado(ghz(n), nivel)
            assert got == reference(n, nivel), f"Con n = {n} y nivel = {nivel} tu función devuelve {got} cx."

