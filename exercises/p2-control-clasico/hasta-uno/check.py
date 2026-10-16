from qgcheck import aer_counts, gates, learner, visible


@visible("el circuito tiene un while_loop y un bit clásico")
def test_structure():
    qc = learner.hasta_uno()
    assert qc.num_clbits == 1, f"El circuito tiene {qc.num_clbits} bits clásicos y debe tener uno."
    assert gates(qc)["while_loop"] == 1, "Falta un `while_loop` que repita la moneda."


@visible("el 1 sale del bucle, sin ninguna puerta X")
def test_no_x_gate():
    assert gates(learner.hasta_uno())["x"] == 0, "El 1 debe salir del bucle que repite la moneda, no de una puerta X."


@visible("el resultado final es siempre 1")
def test_always_one():
    got = dict(aer_counts(learner.hasta_uno(), shots=500))
    assert set(got) == {"1"}, f"Salen {got}. Busca que solo aparezca 1."


def test_other_seed():
    got = dict(aer_counts(learner.hasta_uno(), shots=2000, seed=3))
    assert set(got) == {"1"}, f"Con seed = 3 y 2000 repeticiones salen {got}."
