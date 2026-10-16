import numpy as np
from qiskit.quantum_info import Operator, Pauli

grande = Operator(np.eye(8))
colocado = grande.compose(Operator(Pauli("XZ")), qargs=[0, 2])   # ✏️ cambia qargs

print(colocado.to_matrix().shape)
