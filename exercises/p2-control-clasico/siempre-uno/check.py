from qgcheck import aer_counts, gates, learner, visible


@visible("el resultado final es siempre 1")
def test_always_one():
    got = dict(aer_counts(learner.siempre_uno))
    assert set(got) == {"1"}, f"Salen {got}. Busca que solo aparezca 1."


@visible("sigue siendo la moneda: una H y la X dentro del if_test")
def test_still_a_coin():
    qc = learner.siempre_uno
    names = gates(qc)
    assert names["h"] == 1 and names["if_else"] == 1, "Cambia solo la condición: la H y el `if_test` deben seguir ahí."
    outside = sum(1 for inst in qc.data if inst.operation.name == "x")
    assert outside == 0 and names["x"] == 1, "La X debe aplicarse dentro del `if_test`, no fuera."


def test_other_seed():
    got = dict(aer_counts(learner.siempre_uno, shots=2000, seed=3))
    assert set(got) == {"1"}, f"Con seed = 3 y 2000 repeticiones salen {got}."
