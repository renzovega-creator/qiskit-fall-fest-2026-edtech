from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible


@visible("tu apuesta es el número de términos de hamiltoniano")
def test_bet():
    assert learner.prediccion == len(learner.hamiltoniano), (
        "Tu apuesta no coincide con `len(hamiltoniano)`. Cuenta los pares de vecinos de una línea de 4 espines y los espines.")


def test_same_hamiltonian():
    lesson = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], 1) for i in range(3)] + [("X", [i], -1) for i in range(4)], num_qubits=4)
    h = learner.hamiltoniano
    assert h.equiv(lesson), f"`hamiltoniano` tiene ahora los términos {h.to_list()}; el hamiltoniano de la lección cambió."
