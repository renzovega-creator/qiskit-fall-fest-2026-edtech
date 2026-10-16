from qgcheck import learner, visible


@visible("tiene 8 parámetros")
def test_parameters():
    got = learner.barato.num_parameters
    assert got == 8, f"Ahora tiene {got} parámetros. Busca 8."


@visible("tiene solo 3 puertas de dos qubits")
def test_two_qubit_gates():
    got = learner.barato.num_nonlocal_gates()
    assert got == 3, f"Ahora tiene {got} puertas de dos qubits. Busca 3."


def test_still_ry_and_cz_on_four_qubits():
    qc = learner.barato
    ops = sorted(qc.count_ops())
    assert qc.num_qubits == 4 and ops == ["cz", "ry"], f"`barato` tiene {qc.num_qubits} qubits y las puertas {ops}."
