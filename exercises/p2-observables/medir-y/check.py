from qiskit import QuantumCircuit

from qgcheck import counts, learner, visible


def prepared(*gates):
    qc = QuantumCircuit(1)
    for name in gates:
        getattr(qc, name)(0)
    return qc


def share_of_ones(preparation):
    shots = 4000
    return counts(learner.medir_en_y(preparation), shots=shots, seed=3).get("1", 0) / shots


@visible("|+i⟩ (valor +1 de Y) siempre da 0")
def test_plus_i():
    got = sorted(counts(learner.medir_en_y(prepared("h", "s"))))
    assert got == ["0"], f"Salen {got}. Sin el cambio de base, medir |+i⟩ en Z da 0 o 1 al azar."


@visible("|−i⟩ (valor −1 de Y) siempre da 1")
def test_minus_i():
    got = sorted(counts(learner.medir_en_y(prepared("h", "sdg"))))
    assert got == ["1"], f"Salen {got}. |−i⟩ tiene valor −1 de Y: el bit debe ser 1."


def test_eigenstates_of_x_and_z_are_random():
    for gates in (("h",), ()):
        share = share_of_ones(prepared(*gates))
        assert abs(share - 0.5) < 0.05, f"Con la preparación {gates or 'vacía'} y seed = 3, el bit 1 sale en una fracción {round(share, 2)} de las veces."


def test_input_is_not_modified():
    original = prepared("h", "s")
    learner.medir_en_y(original)
    names = [i.operation.name for i in original.data]
    assert names == ["h", "s"], f"Después de llamar a `medir_en_y`, la preparación original tiene las puertas {names}."
