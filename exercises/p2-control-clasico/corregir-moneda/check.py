from qgcheck import aer_counts, learner, visible


@visible("tu apuesta es el resultado final de la moneda")
def test_bet():
    got = aer_counts(learner.moneda)
    real = next(iter(got)) if len(got) == 1 else "azar"
    assert learner.prediccion == real, (
        "Tu apuesta no coincide con el resultado de `moneda`. Sigue las dos ramas: qué pasa si la moneda sale 0 y qué pasa si sale 1.")


def test_same_circuit():
    got = sorted(aer_counts(learner.moneda, shots=2000, seed=3))
    assert got == ["0"], f"Con seed = 3, `moneda` termina en {got}; el circuito de la lección cambió."
