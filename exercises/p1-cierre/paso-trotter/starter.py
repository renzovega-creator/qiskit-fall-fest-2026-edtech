from qiskit import QuantumCircuit


def paso_trotter(J, h, dt):
    paso = QuantumCircuit(2)
    paso.rzz(0.0, 0, 1)   # ✏️ ángulo en función de J y dt
    paso.rx(0.0, 0)       # ✏️ ángulo en función de h y dt
    paso.rx(0.0, 1)       # ✏️
    return paso


print(paso_trotter(1.0, 0.5, 0.1).draw())
