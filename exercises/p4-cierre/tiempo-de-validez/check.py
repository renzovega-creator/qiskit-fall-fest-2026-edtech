from qgcheck import learner, visible


@visible("devuelve el primer instante en que la medida se aleja más que la tolerancia")
def test_first_time():
    got = learner.tiempo_de_validez([0, 1, 2, 3], [1, 1, 1, 1], [1, 0.95, 0.8, 0.5], 0.1)
    assert got == 2, f"Con errores [0, 0.05, 0.2, 0.5] y tol = 0.1, `tiempo_de_validez` devuelve {got!r}."


@visible("si nunca supera la tolerancia, devuelve None")
def test_never():
    got = learner.tiempo_de_validez([0, 1], [1, 1], [1, 1.05], 0.1)
    assert got is None, f"Con errores [0, 0.05] y tol = 0.1, `tiempo_de_validez` devuelve {got!r}."


def test_after_a_dip():
    got = learner.tiempo_de_validez([0, 1, 2, 3, 4], [1, 1, 1, 1, 1], [1, 0.7, 1, 1, 0.6], 0.2)
    assert got == 1, f"Con errores [0, 0.3, 0, 0, 0.4] y tol = 0.2, `tiempo_de_validez` devuelve {got!r}."


def test_error_equal_to_tolerance():
    got = learner.tiempo_de_validez([0, 1, 2], [0, 0, 0], [0, 0.5, 0.75], 0.5)
    assert got == 2, f"Con errores [0, 0.5, 0.75] y tol = 0.5, `tiempo_de_validez` devuelve {got!r}."


def test_measure_above_reference():
    got = learner.tiempo_de_validez([0.0, 0.5, 1.0], [0, 0, 0], [0, 0.05, -0.4], 0.1)
    assert got == 1.0, f"Con la medida [0, 0.05, -0.4], la referencia [0, 0, 0] y tol = 0.1, `tiempo_de_validez` devuelve {got!r}."
