from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def es_isa(circuito, target):
    # ✏️ recorre circuito.data y pregunta al target por cada instrucción
    return False


isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
print("transpilado:", es_isa(isa, backend.target), "· original:", es_isa(qc, backend.target))
