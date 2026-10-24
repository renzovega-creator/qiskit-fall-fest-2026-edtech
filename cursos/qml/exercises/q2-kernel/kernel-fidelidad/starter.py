from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector

mapa = zz_feature_map(2, reps=1)


def estado(x):
    # el feature map lleva el punto x (dos números) a un estado de 2 qubits
    return Statevector(mapa.assign_parameters(x))


def kernel(x, y):
    # ✏️ similitud cuántica: |⟨φ(y)|φ(x)⟩|²
    return 0.0


print(kernel([0.2, 0.7], [0.2, 0.7]), kernel([0.2, 0.7], [0.9, 0.1]))
