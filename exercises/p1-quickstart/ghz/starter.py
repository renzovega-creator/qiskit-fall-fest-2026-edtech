from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler


def ghz(n):
    qc = QuantumCircuit(n)
    # ✏️ tu código aquí
    qc.measure_all()
    return qc


resultado = StatevectorSampler(seed=7).run([ghz(3)], shots=1024).result()
print(resultado[0].data.meas.get_counts())
