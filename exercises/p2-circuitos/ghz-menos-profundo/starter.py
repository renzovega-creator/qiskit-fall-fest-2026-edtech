from qiskit import QuantumCircuit

ghz6 = QuantumCircuit(6)
ghz6.h(0)
# ✏️ cambia esta escalera por algo más rápido
for k in range(5):
    ghz6.cx(k, k + 1)

print("profundidad:", ghz6.depth())
