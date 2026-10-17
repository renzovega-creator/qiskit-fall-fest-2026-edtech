from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


def paso(n, J, h, dt):
    qc = QuantumCircuit(n)
    for i in range(n - 1):
        qc.rzz(2 * J * dt, i, i + 1)
    for i in range(n):
        qc.rx(2 * h * dt, i)
    return qc


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        qc.compose(paso(n, J, h, dt), inplace=True)
    return qc


def magnetizacion(n, eje="Z"):
    terminos = [(eje, [i], 1 / n) for i in range(n)]
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


def curva_trotter(n, J, h, dt, K):
    valores = []
    for k in range(K + 1):
        estado = Statevector(trotter(n, J, h, dt, k))
        valores.append(float(estado.expectation_value(magnetizacion(n)).real))
    return valores


print(curva_trotter(2, 1.0, 0.5, 0.1, 3))
