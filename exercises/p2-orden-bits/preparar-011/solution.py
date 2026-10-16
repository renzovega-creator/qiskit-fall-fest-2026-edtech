from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

preparado = QuantumCircuit(3)
preparado.x([0, 1])

print(Statevector(preparado).probabilities().round(2))
