from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer.primitives import SamplerV2

q = QuantumRegister(1, "q")
c = ClassicalRegister(1, "c")
moneda = QuantumCircuit(q, c)
moneda.h(q[0])
moneda.measure(q[0], c[0])
with moneda.if_test((c[0], 1)):
    moneda.x(q[0])
moneda.measure(q[0], c[0])

prediccion = "0"

resultado = SamplerV2(seed=11).run([moneda], shots=512).result()[0].data.c.get_counts()
print(resultado)
