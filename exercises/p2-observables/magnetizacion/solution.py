from qiskit.quantum_info import SparsePauliOp


def magnetizacion(n, eje="Z"):
    terminos = []
    for i in range(n):
        terminos.append((eje, [i], 1 / n))
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


print(magnetizacion(4))
