from qiskit import QuantumCircuit

bell13 = QuantumCircuit(5)
bell13.h(1)
bell13.cx(1, 3)
bell13.measure_active()

para_estimator = bell13.remove_final_measurements(inplace=False)
print(bell13.num_clbits, "bits clásicos")
