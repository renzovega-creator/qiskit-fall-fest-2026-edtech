from qgcheck import inside, learner, visible


@inside
def drawing():
    return str(learner.dibujo)


@visible("el dibujo no tiene barreras")
def test_no_barriers():
    assert "░" not in drawing(), "Todavía se ven las barreras (`░`) en el dibujo."


@visible("el qubit 0 está abajo")
def test_reversed():
    text = drawing()
    assert "q_2" in text and "q_0" in text, "El dibujo debe ser de texto y mostrar los tres qubits."
    assert text.index("q_2") < text.index("q_0"), "Todavía q₀ está arriba en el dibujo."


def test_circuit_keeps_its_barrier():
    ops = dict(learner.circuito.count_ops())
    assert ops.get("barrier") == 1 and ops.get("measure") == 3, f"`circuito` tiene ahora las operaciones {ops}; el dibujo no debería cambiarlo."
