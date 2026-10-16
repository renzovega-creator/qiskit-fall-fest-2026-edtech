from qiskit.circuit.library import RXXGate
from qiskit.quantum_info import Operator

from qgcheck import learner, visible


@visible("el circuito importado tiene una puerta rxx")
def test_imported():
    assert learner.antiguo is not None, "Todavía no se importa: `antiguo` vale None."
    assert dict(learner.antiguo.count_ops()) == {"rxx": 1}, f"El circuito tiene {dict(learner.antiguo.count_ops())} y debería tener una `rxx`."


def test_same_gate():
    antiguo = learner.antiguo
    assert antiguo is not None, "`antiguo` vale None."
    params = [list(inst.operation.params) for inst in antiguo.data]
    assert Operator(antiguo) == Operator(RXXGate(0.5)), (
        f"`antiguo` tiene las operaciones {dict(antiguo.count_ops())} con parámetros {params}; su operador no es el del programa de la lección.")
