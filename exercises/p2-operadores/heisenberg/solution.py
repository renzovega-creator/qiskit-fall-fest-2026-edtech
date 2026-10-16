import numpy as np
from qiskit.quantum_info import SparsePauliOp


def heisenberg(n):
    terminos = []
    for i in range(n - 1):
        for cadena in ("XX", "YY", "ZZ"):
            terminos.append((cadena, [i, i + 1], 1))
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


print(np.sort(np.linalg.eigvalsh(heisenberg(2).to_matrix())))
