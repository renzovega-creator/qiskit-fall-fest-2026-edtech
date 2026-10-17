import numpy as np
from scipy.linalg import expm
from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible


def exact(n, J, h, dt, K):
    """⟨M_Z⟩ en los tiempos k·dt con la evolución exacta, desde |0…0⟩."""
    terms = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    H = SparsePauliOp.from_sparse_list(terms, num_qubits=n).to_matrix()
    Mz = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n).to_matrix()
    U = expm(-1j * H * dt)
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    values = []
    for _ in range(K + 1):
        values.append(float(np.real(np.vdot(psi, Mz @ psi))))
        psi = U @ psi
    return np.array(values)


def curve(n, J, h, dt, K):
    return np.asarray(learner.curva_trotter(n, J, h, dt, K), dtype=float)


@visible("con 4 espines y 20 pasos hay 21 puntos, el primero vale 1 y la curva sigue a la exacta")
def test_curve():
    got = curve(4, 1.0, 0.5, 0.1, 20)
    assert got.shape == (21,), f"Con n = 4 y K = 20, `curva_trotter` devuelve {got.size} valores y deben ser 21."
    assert np.isclose(got[0], 1), f"El primer punto de la curva es {round(got[0], 3)} y la cadena empieza con todos los espines en |0⟩."
    worst = np.max(np.abs(got - exact(4, 1.0, 0.5, 0.1, 20)))
    assert worst < 0.02, f"La curva de Trotter se aparta de la exacta hasta {worst:.3f}; el error debe ser menor que 0.02."


@visible("sin campo (h = 0) la magnetización se queda en 1")
def test_no_field():
    got = curve(3, 1.0, 0.0, 0.2, 5)
    assert got.shape == (6,) and np.allclose(got, 1), f"Con n = 3, h = 0 y K = 5, `curva_trotter` devuelve {np.round(got, 2).tolist()}."


def test_zero_steps():
    got = curve(2, 1.0, 0.5, 0.1, 0)
    assert got.shape == (1,), f"Con K = 0, `curva_trotter` devuelve {got.size} valores."


def test_without_coupling():
    got = curve(2, 0.0, 0.5, 0.2, 5)
    assert got.shape == (6,) and np.allclose(got, exact(2, 0.0, 0.5, 0.2, 5), atol=1e-6), (
        f"Con n = 2, J = 0, h = 0.5, dt = 0.2 y K = 5, `curva_trotter` devuelve {np.round(got, 3).tolist()}.")


def test_three_spins():
    got = curve(3, 0.7, 0.4, 0.1, 8)
    assert got.shape == (9,) and np.max(np.abs(got - exact(3, 0.7, 0.4, 0.1, 8))) < 0.02, (
        f"Con n = 3, J = 0.7, h = 0.4, dt = 0.1 y K = 8, `curva_trotter` devuelve {np.round(got, 3).tolist()}.")
