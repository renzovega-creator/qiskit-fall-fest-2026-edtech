import numpy as np

from qgcheck import hint, learner, visible


def referencia(xs, ys):
    """La matriz del kernel por otro camino que la solución: el estado es la primera columna del
    operador del feature map (U|00⟩), sin Statevector. Coincide con FidelityStatevectorKernel de
    Qiskit Machine Learning, que el corredor no instala."""
    from qiskit.circuit.library import zz_feature_map
    from qiskit.quantum_info import Operator

    mapa = zz_feature_map(2, reps=1)

    def phi(x):
        return Operator(mapa.assign_parameters(list(x))).data[:, 0]

    return np.array([[abs(np.vdot(phi(y), phi(x))) ** 2 for y in ys] for x in xs])


@visible("k(x, x) = 1")
@hint(1)
def test_diagonal():
    for x in ([0.2, 0.7], [0.9, 0.1]):
        v = learner.kernel(x, x)
        assert abs(v - 1) < 1e-6, f"kernel({x}, {x}) vale {v:.4f}: el solapamiento de un estado consigo mismo es 1."


@visible("coincide con FidelityStatevectorKernel en dos pares")
@hint(2)
def test_referencia():
    a, b, c = [0.2, 0.7], [0.25, 0.65], [0.9, 0.1]
    ref = referencia([a], [b, c])[0]
    for y, want in zip((b, c), ref, strict=True):
        v = learner.kernel(a, y)
        assert abs(v - want) < 1e-6, f"kernel({a}, {y}) vale {v:.4f} y debería valer {want:.4f}."


def test_aleatorio():
    rng = np.random.default_rng(3)
    xs, ys = rng.random((3, 2)), rng.random((3, 2))
    ref = referencia(xs, ys)
    for i in range(3):
        for j in range(3):
            v = learner.kernel(list(xs[i]), list(ys[j]))
            assert abs(v - ref[i, j]) < 1e-6, "Con otros puntos tu kernel no coincide con el de referencia."
            assert abs(v - learner.kernel(list(ys[j]), list(xs[i]))) < 1e-9, "Tu kernel no es simétrico: k(x, y) debe ser igual a k(y, x)."
