from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def preparar(k, n):
    qc = QuantumCircuit(n)
    # ✏️ añade las X que correspondan a los bits de k
    return qc


print(Statevector(preparar(5, 4)).probabilities().round(2))
