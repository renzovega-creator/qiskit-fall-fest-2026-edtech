from qgcheck import counts, learner, state, visible


@visible("solo aparece la cadena '01'")
def test_only_01():
    got = sorted(counts(learner.emparejado))
    assert got == ["01"], f"Ahora salen {got}. Busca que solo aparezca '01'."


def test_qubit_2_is_still_one():
    probs = {str(k): round(float(v), 2) for k, v in state(learner.emparejado).probabilities_dict().items() if round(float(v), 2)}
    assert probs == {"100": 1.0}, f"Antes de medir, las probabilidades de `emparejado` son {probs}; las puertas no deben cambiar."


def test_other_seed():
    got = sorted(counts(learner.emparejado, shots=1000, seed=3))
    assert got == ["01"], f"Con seed = 3 salen {got}."
