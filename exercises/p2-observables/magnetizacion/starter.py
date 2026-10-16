from qiskit.quantum_info import SparsePauliOp


def magnetizacion(n, eje="Z"):
    terminos = []
    # ✏️ llena `terminos` con las tripletas que pide from_sparse_list
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


print(magnetizacion(4))
