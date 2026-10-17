from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def transpilar(circuito, nivel):
    # ✏️ crea el pass manager con ese nivel, el backend y seed_transpiler=1, y córrelo con el circuito
    return circuito


for nivel in range(4):
    isa = transpilar(qc, nivel)
    print(f"nivel {nivel}: profundidad {isa.depth()}, {isa.count_ops().get('cz', 0)} cz")
