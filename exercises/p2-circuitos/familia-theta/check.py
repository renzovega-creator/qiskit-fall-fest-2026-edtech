import numpy as np

from qgcheck import counts, learner, state, visible

ANGLES = np.linspace(0, np.pi, 21)


def p11(circuit):
    return state(circuit).probabilities_dict().get("11", 0.0)


@visible("hay 21 circuitos sin parámetros libres")
def test_family_size():
    familia = learner.familia
    assert len(familia) == 21, f"Hay {len(familia)} circuitos y deben ser 21."
    free = [c for c in familia if c.num_parameters]
    assert not free, "Algún circuito de `familia` aún tiene el parámetro libre: asígnale un valor con `assign_parameters`."


@visible("la probabilidad de 11 sigue sin²(θ/2)")
def test_sampled_curve():
    familia = learner.familia
    assert len(familia) == 21, "Faltan los 21 circuitos."
    shots = 4000
    got = np.array([counts(c, shots=shots, seed=1).get("11", 0) / shots for c in familia])
    worst = np.max(np.abs(got - np.sin(ANGLES / 2) ** 2))
    assert worst < 0.05, f"Las probabilidades de `11` se alejan de sin²(θ/2) hasta {worst:.2f}."


def test_base_keeps_its_parameter():
    free = learner.base.num_parameters
    assert free == 1, f"Después de generar `familia`, `base` tiene {free} parámetros libres."


def test_exact_angles():
    familia = learner.familia
    assert len(familia) == 21, f"`familia` tiene {len(familia)} circuitos."
    exact = np.array([p11(c) for c in familia])
    off = np.flatnonzero(~np.isclose(exact, np.sin(ANGLES / 2) ** 2, atol=1e-9))
    assert not off.size, f"En el circuito {off[0]} de `familia`, la probabilidad de `11` es {round(exact[off[0]], 3)}."
