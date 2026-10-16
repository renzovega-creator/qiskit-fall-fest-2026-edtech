import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

theta = Parameter("θ")
base = QuantumCircuit(2)
# ✏️ completa base, una sola vez, con el parámetro theta

familia = []   # ✏️ 21 circuitos derivados de base
print(len(familia), "circuitos")
