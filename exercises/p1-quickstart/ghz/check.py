import numpy as np

from qgcheck import counts, learner, state, visible


def only_extremes(n):
    got = sorted(counts(learner.ghz(n)))
    assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}, y deberían salir solo {'0' * n} y {'1' * n}."


@visible("el circuito tiene n qubits y los mide")
def test_size():
    for n in (2, 5):
        qc = learner.ghz(n)
        assert qc.num_qubits == n, f"Con n = {n} el circuito tiene {qc.num_qubits} qubits."
        assert qc.num_clbits == n, f"Con n = {n} el circuito mide {qc.num_clbits} qubits: falta `measure_all()`."


@visible("n = 2, 3 y 4")
def test_small():
    for n in (2, 3, 4):
        only_extremes(n)


def test_larger():
    for n in (5, 7):
        got = sorted(counts(learner.ghz(n)))
        assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}."


def test_state():
    ghz5 = np.zeros(2**5)
    ghz5[0] = ghz5[-1] = 1 / np.sqrt(2)
    probs = {str(k): round(float(v), 2) for k, v in state(learner.ghz(5)).probabilities_dict().items() if round(float(v), 2)}
    assert state(learner.ghz(5)).equiv(ghz5), f"Con n = 5, antes de medir, las probabilidades son {probs}."
