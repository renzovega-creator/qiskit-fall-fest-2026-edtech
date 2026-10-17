from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

# El qubit físico 1 tiene tres vecinos (0, 2 y 3); el 0 solo tiene uno.
chip = CouplingMap([[0, 1], [1, 2], [1, 3], [3, 4]])
chip.make_symmetric()

estrella = QuantumCircuit(4)
estrella.cx(0, 1)
estrella.cx(0, 2)
estrella.cx(0, 3)

# el elemento i es el qubit físico donde va el virtual i
layout_inicial = [0, 1, 2, 3]   # ✏️ ¿en qué qubit físico va el virtual 0?

pm = generate_preset_pass_manager(0, coupling_map=chip, initial_layout=layout_inicial, seed_transpiler=1)
print("swaps:", pm.run(estrella).count_ops().get("swap", 0))
