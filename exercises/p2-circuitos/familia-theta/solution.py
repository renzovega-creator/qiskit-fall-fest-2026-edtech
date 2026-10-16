import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

theta = Parameter("θ")
base = QuantumCircuit(2)
base.rx(theta, 0)
base.cx(0, 1)
base.measure_all()

familia = [base.assign_parameters({theta: valor}) for valor in np.linspace(0, np.pi, 21)]
print(len(familia), "circuitos")
