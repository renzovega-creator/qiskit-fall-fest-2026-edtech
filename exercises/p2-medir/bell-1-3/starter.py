from qiskit import QuantumCircuit

bell13 = QuantumCircuit(5)
# ✏️ entrelaza los qubits 1 y 3 y mídelos con measure_active()

para_estimator = bell13   # ✏️ el mismo circuito, sin mediciones
print(bell13.num_clbits, "bits clásicos")
