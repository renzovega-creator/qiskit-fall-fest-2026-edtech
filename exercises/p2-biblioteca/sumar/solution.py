from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import FullAdderGate
from qiskit.primitives import StatevectorSampler


def sumar(x, y):
    a = QuantumRegister(4, "a")
    b = QuantumRegister(4, "b")
    cout = QuantumRegister(1, "cout")
    qregs = [QuantumRegister(1, "cin"), a, b, cout]
    res = ClassicalRegister(5, "res")
    qc = QuantumCircuit(*qregs, res)
    qc.initialize(x, a)
    qc.initialize(y, b)
    qc.append(FullAdderGate(4), qc.qubits)
    qc.measure([*b, *cout], res)
    return qc


print(StatevectorSampler(seed=5).run([sumar(5, 6)], shots=64).result()[0].data.res.get_int_counts())
