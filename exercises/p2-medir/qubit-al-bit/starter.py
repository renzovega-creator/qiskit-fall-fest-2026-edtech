from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

emparejado = QuantumCircuit(3, 2)
emparejado.x(2)
emparejado.measure([0, 2], [0, 1])   # ✏️ qubits y bits en el orden que pide el enunciado

conteos = StatevectorSampler(seed=7).run([emparejado], shots=256).result()[0].data.c.get_counts()
print(conteos)
