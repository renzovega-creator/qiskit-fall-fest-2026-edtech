from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

circuito = QuantumCircuit(3)
circuito.x([0, 2])
circuito.measure_all()

prediccion = ""   # ✏️ tu apuesta, entre comillas: ¿qué cadena de bits devuelve Qiskit?

medido = StatevectorSampler(seed=7).run([circuito], shots=128).result()[0].data.meas.get_counts()
# compruébalo con print(medido)
