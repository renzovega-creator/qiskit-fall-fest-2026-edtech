import numpy as np
from qiskit.quantum_info import Statevector

from qgcheck import learner, visible


@visible("el estado es |011⟩")
def test_state():
    probs = Statevector(learner.preparado).probabilities_dict()
    assert np.isclose(probs.get("011", 0), 1), f"Ahora el estado es {[str(k) for k in probs]}. Busca `011`: q₀ = 1, q₁ = 1 y q₂ = 0."


def test_index_three_without_phase():
    vector = Statevector(learner.preparado).data
    top = int(np.argmax(abs(vector)))
    assert vector.shape == (8,) and np.isclose(vector[3], 1), (
        f"`preparado` tiene {vector.shape[0]} amplitudes; la mayor, {np.round(vector[top], 3)}, está en el índice {top}.")
