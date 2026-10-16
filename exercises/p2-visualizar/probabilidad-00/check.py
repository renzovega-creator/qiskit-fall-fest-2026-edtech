from math import pi

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from qgcheck import learner, visible


@visible("tu apuesta es P(00)")
def test_bet():
    real = learner.psi.probabilities_dict()["00"]
    bet = learner.prediccion
    assert bet is not None and abs(bet - real) < 0.01, (
        "Tu apuesta está lejos de P(00). Piensa qué hace la H sobre q₀ y qué hace la RX controlada en cada rama.")


def test_same_state():
    lesson = QuantumCircuit(2)
    lesson.h(0)
    lesson.crx(pi / 2, 0, 1)
    probs = {str(k): round(float(v), 2) for k, v in learner.psi.probabilities_dict().items()}
    assert learner.psi.equiv(Statevector(lesson)), f"`psi` da ahora las probabilidades {probs}; el estado de la lección cambió."
