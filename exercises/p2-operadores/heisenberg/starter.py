import numpy as np
from qiskit.quantum_info import SparsePauliOp


def heisenberg(n):
    terminos = []
    # ✏️ llena `terminos` con las tripletas que pide from_sparse_list
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


print(np.sort(np.linalg.eigvalsh(heisenberg(2).to_matrix())))
