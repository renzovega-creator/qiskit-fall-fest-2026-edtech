"""Cadena de espines de Ising con campo transversal: el código del proyecto del curso.

    H = J · Σ Z_i Z_{i+1} + h · Σ X_i

El sistema empieza en |0…0⟩ y evoluciona con pasos de Trotter. La magnetización
media M = (1/n) · Σ ⟨Z_i⟩ sigue el experimento. Las funciones de ejecución
usan las primitivas del lado del cliente de qiskit-ibm-runtime
(`executor_estimator.Estimator` y `executor_sampler.Sampler`), así que `mode` puede
ser un backend real, un `Batch`, una `Session` o un backend falso para probar
en local.

    from ising import estimador, curva
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    backend = FakeManilaV2()
    medida = curva(estimador(backend), backend, n=4, pasos=8, J=1, h=1, dt=0.2)
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from scipy.linalg import expm

__all__ = [
    "hamiltoniano",
    "magnetizacion",
    "circuito",
    "exacta",
    "estimador",
    "sampler",
    "curva",
]


def hamiltoniano(n, J, h):
    """Hamiltoniano de la cadena abierta de n espines."""
    terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


def magnetizacion(n):
    """Observable M = (1/n) · Σ Z_i."""
    return SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)


def circuito(n, pasos, J, h, dt):
    """`pasos` pasos de Trotter: rzz en cada par vecino y rx en cada espín."""
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def exacta(n, J, h, dt, pasos):
    """Magnetización exacta en los tiempos 0, dt, …, pasos·dt."""
    U = expm(-1j * hamiltoniano(n, J, h).to_matrix() * dt)
    M = magnetizacion(n).to_matrix()
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    valores = []
    for _ in range(pasos + 1):
        valores.append(float(np.real(np.vdot(psi, M @ psi))))
        psi = U @ psi
    return valores


def estimador(mode):
    """Estimator del lado del cliente sobre un backend, un Batch o una Session."""
    from qiskit_ibm_runtime.executor_estimator import Estimator

    return Estimator(mode=mode)


def sampler(mode):
    """Sampler del lado del cliente sobre un backend, un Batch o una Session."""
    from qiskit_ibm_runtime.executor_sampler import Sampler

    return Sampler(mode=mode)


def curva(est, backend, n, pasos, J, h, dt, nivel=1):
    """Magnetización medida en los tiempos 0, dt, …, pasos·dt, en un solo trabajo."""
    pm = generate_preset_pass_manager(nivel, backend=backend, seed_transpiler=1)
    M = magnetizacion(n)
    pubs = []
    for k in range(pasos + 1):
        isa = pm.run(circuito(n, k, J, h, dt))
        pubs.append((isa, M.apply_layout(isa.layout)))
    return [float(r.data.evs) for r in est.run(pubs).result()]
