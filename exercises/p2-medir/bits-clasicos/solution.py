from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(3, 1)
qc.x([0, 2])
qc.measure_all()

prediccion = 4

conteos = StatevectorSampler(seed=7).run([qc], shots=256).result()[0].data.meas.get_counts()
print(qc.num_clbits, conteos)
