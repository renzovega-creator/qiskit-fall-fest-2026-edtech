import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler


def circuito(theta):
    qc = QuantumCircuit(1)
    qc.ry(theta, 0)
    qc.measure_all()
    return qc


def estimar_p(theta, shots):
    res = StatevectorSampler(seed=7).run([circuito(theta)], shots=shots).result()
    conteos = res[0].data.meas.get_counts()
    return conteos.get("1", 0) / shots


print(estimar_p(np.pi / 3, 1000), "≈", np.sin(np.pi / 6) ** 2)
