import numpy as np

from qgcheck import learner, state, visible


@visible("prepara el mismo estado GHZ de 6 qubits")
def test_same_state():
    ghz = np.zeros(2**6)
    ghz[0] = ghz[-1] = 1 / np.sqrt(2)
    qc = learner.ghz6
    assert qc.num_qubits == 6, f"El circuito tiene {qc.num_qubits} qubits y debe tener 6."
    assert state(qc).equiv(ghz), "El estado ya no es el GHZ de 6 qubits."


@visible("profundidad 4 o menos")
def test_depth():
    depth = learner.ghz6.depth()
    assert depth <= 4, f"La profundidad es {depth}. Busca 4 o menos."


def test_only_one_and_two_qubit_gates():
    wide = [inst.operation.name for inst in learner.ghz6.data if len(inst.qubits) > 2]
    assert not wide, f"`ghz6` contiene las puertas {wide}."
