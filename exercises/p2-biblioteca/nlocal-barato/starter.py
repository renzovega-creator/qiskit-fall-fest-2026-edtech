from qiskit.circuit.library import n_local

barato = n_local(4, "ry", "cz")   # ✏️ añade los argumentos que faltan
print(barato.num_parameters, "parámetros")
print(barato.num_nonlocal_gates(), "puertas de dos qubits")
