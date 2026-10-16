import numpy as np
from qiskit.quantum_info import Statevector

from qgcheck import learner, visible


def prepared(k, n):
    qc = learner.preparar(k, n)
    assert qc.num_qubits == n, f"Con k = {k} y n = {n}, el circuito tiene {qc.num_qubits} qubits."
    return qc


def amplitude_at(k, n):
    return Statevector(prepared(k, n)).data


@visible("preparar(5, 4) deja la amplitud en el índice 5")
def test_example():
    vector = amplitude_at(5, 4)
    assert np.isclose(abs(vector[5]), 1), f"Con k = 5 y n = 4 la amplitud está en el índice {int(np.argmax(abs(vector)))}."


@visible("los 16 valores de k con n = 4")
def test_four_qubits():
    for k in range(16):
        vector = amplitude_at(k, 4)
        assert np.isclose(abs(vector[k]), 1), f"Con k = {k} la amplitud no está en el índice {k}."


def test_other_sizes():
    for n in (1, 3, 6):
        for k in range(2**n):
            vector = amplitude_at(k, n)
            assert np.isclose(abs(vector[k]), 1), f"Con k = {k} y n = {n}, la amplitud está en el índice {int(np.argmax(abs(vector)))}."


def test_no_measurements_no_phase():
    for k, n in ((6, 3), (37, 6)):
        qc = prepared(k, n)
        assert qc.num_clbits == 0, f"Con k = {k} y n = {n}, el circuito tiene {qc.num_clbits} bits clásicos."
        amplitude = Statevector(qc).data[k]
        assert np.isclose(amplitude, 1), f"Con k = {k} y n = {n}, la amplitud del índice {k} es {np.round(amplitude, 3)}."
