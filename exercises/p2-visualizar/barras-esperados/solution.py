import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp


def valores_esperados(circuito, etiquetas):
    obs = np.fromiter([SparsePauliOp(e) for e in etiquetas], dtype=object).reshape(len(etiquetas), 1)
    res = StatevectorEstimator().run([(circuito, obs)]).result()[0]
    return res.data.evs.flatten()


def graficar(circuito, etiquetas):
    """Dibuja una barra por etiqueta con su valor esperado y devuelve los ejes."""
    figura, ejes = plt.subplots()
    ejes.bar(etiquetas, valores_esperados(circuito, etiquetas))
    return ejes


bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
print(valores_esperados(bell, ["ZZ", "XX", "YY", "ZI", "IZ"]))
