from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

emparejado = QuantumCircuit(3, 2)
emparejado.x(2)
emparejado.measure([2, 0], [0, 1])

conteos = StatevectorSampler(seed=7).run([emparejado], shots=256).result()[0].data.c.get_counts()
print(conteos)
