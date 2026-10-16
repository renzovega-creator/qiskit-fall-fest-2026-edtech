import numpy as np
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from qgcheck import counts, learner, state, visible


def expectation(circuit, pauli):
    obs = SparsePauliOp.from_sparse_list([(pauli, [1, 3], 1)], num_qubits=5)
    return float(StatevectorEstimator().run([(circuit, obs)]).result()[0].data.evs)


@visible("bell13 mide solo los qubits 1 y 3 y da 00 y 11")
def test_sampler():
    qc = learner.bell13
    assert qc.num_clbits == 2, f"`bell13` tiene {qc.num_clbits} bits clásicos y debe tener 2."
    got = sorted(counts(qc))
    assert got == ["00", "11"], f"Salen {got}, y deberían salir solo 00 y 11."


@visible("para_estimator no tiene mediciones y los qubits 1 y 3 forman un Bell")
def test_estimator():
    qc = learner.para_estimator
    assert qc.num_clbits == 0, "`para_estimator` no debe tener bits clásicos ni mediciones."
    zz, xx = expectation(qc, "ZZ"), expectation(qc, "XX")
    assert np.isclose(zz, 1) and np.isclose(xx, 1), f"⟨Z₁Z₃⟩ vale {zz:.2f} y ⟨X₁X₃⟩ vale {xx:.2f}; en un Bell valen 1 y 1."


def test_same_state_for_both():
    a, b = state(learner.bell13), state(learner.para_estimator)
    overlap = abs(a.inner(b)) ** 2
    assert a.equiv(b), f"El solapamiento entre el estado de `bell13` y el de `para_estimator` es {round(overlap, 2)}."


def test_idle_qubits_untouched():
    qc = learner.bell13
    busy = sorted({qc.find_bit(q).index for inst in qc.data if inst.operation.name != "barrier" for q in inst.qubits})
    assert busy == [1, 3], f"`bell13` usa los qubits {busy}."
