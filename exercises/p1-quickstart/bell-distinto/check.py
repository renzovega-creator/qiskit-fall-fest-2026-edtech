import numpy as np

from qgcheck import counts, gates, learner, state, visible

BELL_DISTINTO = np.array([0, 1, 1, 0]) / np.sqrt(2)


@visible("los qubits salen siempre distintos")
def test_counts():
    got = sorted(counts(learner.anti))
    assert got == ["01", "10"], f"Salen {got}. Busca que solo aparezcan 01 y 10."


@visible("el estado es (|01⟩ + |10⟩)/√2")
def test_state():
    assert state(learner.anti).equiv(BELL_DISTINTO), "El estado antes de medir no es (|01⟩ + |10⟩)/√2."


@visible("añades una sola puerta al estado de Bell")
def test_one_gate():
    names = gates(learner.anti)
    extra = sum(names.values()) - names["barrier"] - names["measure"] - 2
    assert extra == 1, f"Añadiste {extra} puertas a la H y la CNOT; tiene que ser una."


def test_balanced():
    got = counts(learner.anti, shots=4096, seed=99)
    low, high = 2048 - 256, 2048 + 256
    assert low <= got.get("01", 0) <= high, f"Con seed = 99 y 4096 repeticiones salen {dict(sorted(got.items()))}."
