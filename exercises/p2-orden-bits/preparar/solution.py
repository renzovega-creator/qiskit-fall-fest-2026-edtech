from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def preparar(k, n):
    qc = QuantumCircuit(n)
    for j in range(n):
        if (k >> j) & 1:
            qc.x(j)
    return qc


print(Statevector(preparar(5, 4)).probabilities().round(2))
