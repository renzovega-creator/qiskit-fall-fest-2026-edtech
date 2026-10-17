from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer.primitives import SamplerV2


def hasta_uno():
    q = QuantumRegister(1, "q")
    c = ClassicalRegister(1, "c")
    qc = QuantumCircuit(q, c)
    # ✏️ tu código aquí
    return qc


resultado = SamplerV2(seed=11).run([hasta_uno()], shots=500).result()
print(resultado[0].data.c.get_counts())
