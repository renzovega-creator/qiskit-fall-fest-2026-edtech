from qiskit.circuit.library import n_local

from qgcheck import learner, visible


@visible("tu apuesta es el número de parámetros de ansatz")
def test_bet():
    assert learner.prediccion == learner.ansatz.num_parameters, (
        "Tu apuesta no coincide con `ansatz.num_parameters`. Cuenta las capas de rotaciones: son una más que las repeticiones.")


def test_same_circuit():
    lesson = n_local(3, "rx", "cz")
    ansatz = learner.ansatz
    assert ansatz.num_qubits == lesson.num_qubits and ansatz.count_ops() == lesson.count_ops(), (
        f"`ansatz` tiene ahora {ansatz.num_qubits} qubits y las puertas {dict(ansatz.count_ops())}; el circuito de la lección cambió.")
