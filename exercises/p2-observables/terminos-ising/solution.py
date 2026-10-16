from qiskit.quantum_info import SparsePauliOp

n = 4
interacciones = [("ZZ", [i, i + 1], 1) for i in range(n - 1)]
campo = [("X", [i], -1) for i in range(n)]
hamiltoniano = SparsePauliOp.from_sparse_list(interacciones + campo, num_qubits=n)

prediccion = 7
print(len(hamiltoniano))
