import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler


def circuito(theta):
    qc = QuantumCircuit(1)
    # ✏️ rota el qubit un ángulo theta alrededor del eje Y
    qc.measure_all()
    return qc


def estimar_p(theta, shots):
    res = StatevectorSampler(seed=7).run([circuito(theta)], shots=shots).result()
    conteos = res[0].data.meas.get_counts()
    # ✏️ devuelve la frecuencia de '1' (el estimador de Monte Carlo)
    return 0.0


print(estimar_p(np.pi / 3, 1000), "≈", np.sin(np.pi / 6) ** 2)
