import numpy as np
from qiskit.quantum_info import Operator, Pauli

from qgcheck import learner, visible


@visible("tu apuesta es el producto que calcula compose")
def test_bet():
    x, z = Pauli("X").to_matrix(), Pauli("Z").to_matrix()
    product = {"XZ": x @ z, "ZX": z @ x}.get(learner.orden)
    assert product is not None, 'Escribe en `orden` "XZ" o "ZX".'
    assert np.allclose(learner.resultado.data, product), (
        "Tu apuesta no coincide con `resultado`. `A.compose(B)` aplica primero `A`; el producto se escribe de derecha a izquierda.")


def test_same_composition():
    lesson = Operator(Pauli("X")).compose(Operator(Pauli("Z")))
    assert learner.resultado == lesson, (
        f"`resultado` vale ahora {np.round(learner.resultado.data, 2).tolist()}; la composición de la lección cambió.")
