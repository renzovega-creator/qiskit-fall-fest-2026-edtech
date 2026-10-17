from scipy.linalg import expm
from qiskit.quantum_info import Operator, SparsePauliOp

from qgcheck import learner, visible


def exact_step(J, h, dt):
    """e^{-i h dt (X0 + X1)} e^{-i J dt Z0 Z1}, el paso de Trotter exacto."""
    zz = expm(-1j * J * dt * SparsePauliOp("ZZ").to_matrix())
    x = expm(-1j * h * dt * SparsePauliOp.from_list([("IX", 1), ("XI", 1)]).to_matrix())
    return Operator(x @ zz)


def angles(circuit):
    return [round(float(item.operation.params[0]), 3) for item in circuit.data]


def matches(J, h, dt):
    got = learner.paso_trotter(J, h, dt)
    return got, got.num_qubits == 2 and Operator(got).equiv(exact_step(J, h, dt))


@visible("con J = 1, h = 0.5 y dt = 0.1 el circuito es el paso de Trotter")
def test_step():
    got, ok = matches(1.0, 0.5, 0.1)
    assert ok, f"Los ángulos de tu circuito son {angles(got)}; todavía no coincide con el paso de Trotter. ¿Usaste el factor 2?"


@visible("el circuito tiene 2 qubits y una rzz seguida de dos rx")
def test_gates():
    got = learner.paso_trotter(1.0, 0.5, 0.1)
    names = [item.operation.name for item in got.data]
    assert got.num_qubits == 2 and names == ["rzz", "rx", "rx"], f"Tu circuito tiene {got.num_qubits} qubits y las puertas {names}."


def test_other_values():
    got, ok = matches(0.7, 1.2, 0.3)
    assert ok, f"Con J = 0.7, h = 1.2 y dt = 0.3, los ángulos de tu circuito son {angles(got)}."


def test_without_coupling():
    got, ok = matches(0.0, 0.8, 0.25)
    assert ok, f"Con J = 0, h = 0.8 y dt = 0.25, los ángulos de tu circuito son {angles(got)}."


def test_without_field():
    got, ok = matches(1.3, 0.0, 0.4)
    assert ok, f"Con J = 1.3, h = 0 y dt = 0.4, los ángulos de tu circuito son {angles(got)}."
