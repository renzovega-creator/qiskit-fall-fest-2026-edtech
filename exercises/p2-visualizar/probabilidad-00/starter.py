from math import pi

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

estado = QuantumCircuit(2)
estado.h(0)
estado.crx(pi / 2, 0, 1)
psi = Statevector(estado)

prediccion = None   # ✏️ tu apuesta: P(00), un número entre 0 y 1
# compruébalo con print(psi.probabilities().round(2)): el índice es la cadena en binario
