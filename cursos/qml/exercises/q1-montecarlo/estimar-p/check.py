import numpy as np

from qgcheck import hint, learner, state, visible


@visible("circuito(theta) da P(1) = sin²(θ/2)")
@hint(1)
def test_circuito():
    for th in (0.0, np.pi / 3, np.pi / 2, np.pi):
        p1 = float(state(learner.circuito(th)).probabilities()[1])
        want = np.sin(th / 2) ** 2
        assert abs(p1 - want) < 1e-6, f"Con θ = {th:.3f}, P(1) vale {p1:.3f} y debería valer {want:.3f}."


@visible("estimar_p(π/3, 2000) se acerca a 0.25")
@hint(2)
def test_frecuencia():
    p = learner.estimar_p(np.pi / 3, 2000)
    assert 0 <= p <= 1, f"estimar_p devolvió {p}: una frecuencia está entre 0 y 1."
    assert abs(p - 0.25) < 4 * np.sqrt(0.25 * 0.75 / 2000), f"Con θ = π/3 y 2000 shots salió {p:.3f}; debería acercarse a 0.25."


def test_extremos():
    for theta, expected in ((0.0, 0), (np.pi, 1)):
        result = learner.estimar_p(theta, 100)
        assert result == expected, f"`estimar_p({theta!r}, 100)` devolvió {result!r}; revisa los ángulos extremos."
