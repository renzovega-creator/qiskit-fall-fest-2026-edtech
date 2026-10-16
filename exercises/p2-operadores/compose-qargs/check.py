import numpy as np
from qiskit.quantum_info import Operator, Pauli, Statevector

from qgcheck import learner, visible


@visible("el resultado es ZXI")
def test_operator():
    assert learner.colocado == Operator(Pauli("ZXI")), (
        "Todavía no es `ZXI`. El primer elemento de `qargs` es el qubit de destino del qubit 0 de `XZ`.")


def test_acts_on_states():
    start = Statevector.from_label("100")
    want = -1 * Statevector.from_label("110")
    got = start.evolve(learner.colocado)
    amplitudes = {format(i, "03b"): complex(np.round(a, 3)) for i, a in enumerate(got.data) if abs(a) > 1e-9}
    assert got == want, f"Aplicado a |q₂q₁q₀⟩ = |100⟩, `colocado` da {amplitudes}."
