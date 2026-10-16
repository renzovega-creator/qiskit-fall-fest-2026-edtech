import os

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

from qgcheck import learner, visible


def with_flow():
    theta = Parameter("θ")
    qc = QuantumCircuit(1, 1)
    qc.rx(theta, 0)
    qc.measure(0, 0)
    with qc.if_test((qc.clbits[0], 1)):
        qc.x(0)
    return qc


def with_loops():
    a, b = Parameter("a"), Parameter("b")
    qc = QuantumCircuit(2, 2)
    qc.ry(a, 0)
    qc.crz(b, 0, 1)
    with qc.for_loop(range(3)):
        qc.h(1)
    qc.measure([0, 1], [0, 1])
    return qc


def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


@visible("guardar devuelve bytes")
def test_save_returns_bytes():
    data = learner.guardar(with_flow())
    assert isinstance(data, bytes) and data, "`guardar` debe devolver los bytes del archivo QPY, no un texto ni una lista."


@visible("cargar devuelve el mismo circuito, con parámetro y if_test")
def test_round_trip():
    circuit = with_flow()
    loaded = learner.cargar(learner.guardar(circuit))
    assert isinstance(loaded, QuantumCircuit), "`cargar` debe devolver un solo circuito: `qpy.load` devuelve una lista."
    assert loaded == circuit, "El circuito que carga no es igual al que guardaste."


def test_other_circuits():
    for make in (bell, with_loops):
        circuit = make()
        loaded = learner.cargar(learner.guardar(circuit))
        got = dict(loaded.count_ops()) if isinstance(loaded, QuantumCircuit) else type(loaded).__name__
        assert loaded == circuit, f"Con `{make.__name__}()`, `cargar` devuelve {got!r}."


def test_does_not_touch_the_disk():
    before = sorted(os.listdir("."))
    learner.cargar(learner.guardar(bell()))
    created = sorted(set(os.listdir(".")) - set(before))
    assert not created, f"`guardar` y `cargar` dejaron en el disco {created}."
