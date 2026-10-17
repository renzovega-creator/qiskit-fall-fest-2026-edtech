# Equivocada: da las puertas del chip pero no el backend, así que no hay layout ni routing.
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def pass_manager(nivel):
    return generate_preset_pass_manager(optimization_level=nivel, basis_gates=["cz", "rz", "sx", "x"], seed_transpiler=1)


print(sorted(pass_manager(1).run(qc).count_ops()))
