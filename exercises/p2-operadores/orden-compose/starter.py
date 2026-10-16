from qiskit.quantum_info import Operator, Pauli

A = Operator(Pauli("X"))
B = Operator(Pauli("Z"))
resultado = A.compose(B)

orden = ""   # ✏️ "XZ" o "ZX": ¿resultado es el producto X·Z o Z·X?
# compruébalo con print(resultado.data)
