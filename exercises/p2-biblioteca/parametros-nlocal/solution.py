from qiskit.circuit.library import n_local

ansatz = n_local(3, "rx", "cz")

prediccion = 12
print(ansatz.num_parameters)
