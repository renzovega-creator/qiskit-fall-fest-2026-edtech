from qgcheck import learner, visible


@visible("tu apuesta es el número de instrucciones de importado")
def test_bet():
    assert learner.prediccion == len(learner.importado.data), (
        "Tu apuesta no coincide con `len(importado.data)`. Una `measure` sobre un registro de 2 bits son dos instrucciones.")


def test_same_program():
    ops = dict(learner.importado.count_ops())
    assert ops == {"h": 1, "cx": 1, "measure": 2}, f"`importado` tiene ahora las operaciones {ops}; el programa de la lección cambió."
