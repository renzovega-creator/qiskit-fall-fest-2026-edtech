from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector

mapa = zz_feature_map(2, reps=1)


def estado(x):
    return Statevector(mapa.assign_parameters(x))


def kernel(x, y):
    return float(abs(estado(y).inner(estado(x))) ** 2)


print(kernel([0.2, 0.7], [0.2, 0.7]), kernel([0.2, 0.7], [0.9, 0.1]))
