from qiskit import QuantumCircuit

ghz6 = QuantumCircuit(6)
ghz6.h(0)
ghz6.cx(0, 1)
ghz6.cx(0, 2)
ghz6.cx(1, 3)
ghz6.cx(0, 4)
ghz6.cx(1, 5)

print("profundidad:", ghz6.depth())
