from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

preparado = QuantumCircuit(3)
preparado.x(2)   # ✏️ ¿en qué qubits va la X?

print(Statevector(preparado).probabilities().round(2))
