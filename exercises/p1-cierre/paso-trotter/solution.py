from qiskit import QuantumCircuit


def paso_trotter(J, h, dt):
    paso = QuantumCircuit(2)
    paso.rzz(2 * J * dt, 0, 1)
    paso.rx(2 * h * dt, 0)
    paso.rx(2 * h * dt, 1)
    return paso


print(paso_trotter(1.0, 0.5, 0.1).draw())
