from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler


def medir_en_y(preparacion):
    """Devuelve una copia de `preparacion` que mide el qubit 0 en la base Y."""
    qc = preparacion.copy()
    qc.sdg(0)
    qc.h(0)
    qc.measure_all()
    return qc


mas_i = QuantumCircuit(1)
mas_i.h(0)
mas_i.s(0)       # prepara |+i⟩, el autoestado de Y con valor +1

conteos_y = StatevectorSampler(seed=7).run([medir_en_y(mas_i)], shots=512).result()[0].data.meas.get_counts()
print(conteos_y)
