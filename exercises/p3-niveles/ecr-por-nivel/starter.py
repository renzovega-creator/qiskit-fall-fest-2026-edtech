from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import random_unitary
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

backend = FakeSherbrooke()


def unitaria_y_swap(semilla):
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(random_unitary(4, seed=semilla)), range(2))
    qc.swap(0, 1)
    return qc


def ecr_por_nivel(circuito):
    # ✏️ devuelve [ecr con el nivel 0, con el 1, con el 2, con el 3]; transpila con seed_transpiler=12345
    return []


print(ecr_por_nivel(unitaria_y_swap(12345)))
