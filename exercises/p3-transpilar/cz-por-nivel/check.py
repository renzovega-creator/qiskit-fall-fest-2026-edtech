from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, operator, unsupported, visible

TARGET = FakeFez().target


def toffoli():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.ccx(0, 1, 2)
    return qc


def fredkin():
    qc = QuantumCircuit(3)
    qc.h(1)
    qc.cswap(0, 1, 2)
    return qc


def ghz4():
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, [1, 2, 3])
    return qc


def cz(isa):
    return isa.count_ops().get("cz", 0)


@visible("el resultado solo usa instrucciones de FakeFez")
def test_isa():
    bad = unsupported(learner.transpilar(toffoli(), 1), TARGET)
    assert not bad, f"Con nivel = 1 quedan instrucciones que FakeFez no ejecuta: {bad}."


@visible("el circuito sigue haciendo lo mismo")
def test_same_operator():
    isa = learner.transpilar(toffoli(), 2)
    assert operator(isa).equiv(Operator(toffoli())), "Con nivel = 2 el circuito transpilado ya no implementa el mismo operador."


def test_every_level_and_circuit_is_isa():
    for make in (fredkin, ghz4):
        for nivel in range(4):
            bad = unsupported(learner.transpilar(make(), nivel), TARGET)
            assert not bad, f"Con `{make.__name__}()` y nivel = {nivel} quedan instrucciones que FakeFez no ejecuta: {bad}."


def test_every_level_keeps_the_operator():
    for make in (fredkin, ghz4):
        for nivel in range(4):
            isa = learner.transpilar(make(), nivel)
            assert operator(isa).equiv(Operator(make())), (
                f"Con `{make.__name__}()` y nivel = {nivel} el operador cambió; el circuito tiene {dict(isa.count_ops())}.")


def test_the_level_is_used():
    for make in (toffoli, fredkin):
        low, high = cz(learner.transpilar(make(), 0)), cz(learner.transpilar(make(), 3))
        assert high < low, f"Con circuito = {make.__name__}, el nivel 3 deja {high} cz y el nivel 0 deja {low}: no se nota el nivel."
