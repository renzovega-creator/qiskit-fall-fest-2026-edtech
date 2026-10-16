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
    archivo = io.BytesIO()
    qpy.dump(circuito, archivo)
    return archivo.getvalue()


def cargar(datos):
    return qpy.load(io.BytesIO(datos))[0]


print(cargar(guardar(prueba)) == prueba)
