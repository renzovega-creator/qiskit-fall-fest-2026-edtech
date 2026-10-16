import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp


def valores_esperados(circuito, etiquetas):
    # ✏️ calcula con el Estimator el valor esperado de cada etiqueta
    return np.zeros(len(etiquetas))


def graficar(circuito, etiquetas):
    """Dibuja una barra por etiqueta con su valor esperado y devuelve los ejes."""
    figura, ejes = plt.subplots()
    # ✏️ dibuja las barras en `ejes`
    return ejes


bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
print(valores_esperados(bell, ["ZZ", "XX", "YY", "ZI", "IZ"]))
