from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

anti = QuantumCircuit(2)
anti.h(0)
anti.cx(0, 1)
# ✏️ añade aquí tu puerta
anti.measure_all()

resultado = StatevectorSampler(seed=7).run([anti], shots=1024).result()
print(resultado[0].data.meas.get_counts())
