from qgcheck import counts, learner, visible


def total(x, y):
    got = counts(learner.sumar(x, y), shots=64, seed=5)
    return {int(bits, 2): n for bits, n in got.items()}


@visible("5 + 6 = 11")
def test_example():
    got = total(5, 6)
    assert got == {11: 64}, f"`sumar(5, 6)` mide {got}, y debería medir solo 11."


@visible("1 + 2 = 3, 7 + 8 = 15 y 0 + 9 = 9")
def test_more_sums():
    for x, y in ((1, 2), (7, 8), (0, 9)):
        got = total(x, y)
        assert got == {x + y: 64}, f"`sumar({x}, {y})` mide {got}, y debería medir solo {x + y}."


def test_other_numbers():
    for x, y in ((15, 0), (3, 12), (8, 7), (0, 0), (10, 5), (4, 4)):
        got = total(x, y)
        assert got == {x + y: 64}, f"`sumar({x}, {y})` mide {got}."


def test_carry_out():
    for x, y in ((15, 1), (9, 9), (15, 15)):
        got = total(x, y)
        assert got == {x + y: 64}, f"`sumar({x}, {y})` mide {got}."
