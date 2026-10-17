from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer.primitives import SamplerV2

q = QuantumRegister(1, "q")
c = ClassicalRegister(1, "c")
siempre_uno = QuantumCircuit(q, c)
siempre_uno.h(q[0])
siempre_uno.measure(q[0], c[0])
with siempre_uno.if_test((c[0], 1)):   # ✏️ cambia solo esta condición
    siempre_uno.x(q[0])
siempre_uno.measure(q[0], c[0])

resultado = SamplerV2(seed=11).run([siempre_uno], shots=512).result()
print(resultado[0].data.c.get_counts())
