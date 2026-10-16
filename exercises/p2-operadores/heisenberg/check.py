import numpy as np
from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible


def reference(n):
    return sum((SparsePauliOp.from_sparse_list([(p, [i, i + 1], 1)], num_qubits=n)
                for i in range(n - 1) for p in ("XX", "YY", "ZZ")), start=SparsePauliOp("I" * n, 0))


@visible("2 qubits: autovalores −3, 1, 1, 1")
def test_two_spins():
    op = learner.heisenberg(2)
    assert op.num_qubits == 2, f"Con n = 2 el operador tiene {op.num_qubits} qubits."
    eigenvalues = np.sort(np.linalg.eigvalsh(op.to_matrix()))
    assert np.allclose(eigenvalues, [-3, 1, 1, 1]), f"Con n = 2 los autovalores son {np.round(eigenvalues, 2).tolist()}."


@visible("50 qubits: 3 · 49 términos")
def test_fifty_spins():
    op = learner.heisenberg(50)
    assert op.num_qubits == 50 and len(op) == 3 * 49, f"Con n = 50 el operador tiene {len(op)} términos y deberían ser 147."


def test_other_sizes():
    for n in (3, 4, 6):
        op = learner.heisenberg(n)
        assert op.num_qubits == n and op.equiv(reference(n)), (
            f"Con n = {n} el operador tiene los términos {op.paulis.to_labels()}, y no es la cadena de Heisenberg.")
