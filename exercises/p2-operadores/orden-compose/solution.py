from qiskit.quantum_info import Operator, Pauli

A = Operator(Pauli("X"))
B = Operator(Pauli("Z"))
resultado = A.compose(B)

orden = "ZX"
print(resultado.data)
