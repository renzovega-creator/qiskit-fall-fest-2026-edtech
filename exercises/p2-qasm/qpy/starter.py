import io

from qiskit import QuantumCircuit, qpy
from qiskit.circuit import Parameter

theta = Parameter("θ")
prueba = QuantumCircuit(1, 1)
prueba.rx(theta, 0)
prueba.measure(0, 0)
with prueba.if_test((prueba.clbits[0], 1)):
    prueba.x(0)


def guardar(circuito):
    # ✏️ devuelve los bytes del circuito en formato QPY
    return b""


def cargar(datos):
    # ✏️ devuelve el circuito que esos bytes contienen
    return None


print(cargar(guardar(prueba)) == prueba)
