from qiskit.transpiler.passes.synthesis.plugin import (
    high_level_synthesis_plugin_names,
    unitary_synthesis_plugin_names,
)
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

clifford_metodos = []   # ✏️ los métodos para sintetizar un Clifford
unitaria_metodos = []   # ✏️ los métodos para sintetizar una unitaria
routing_metodos = []    # ✏️ los métodos para el routing

print("clifford:", clifford_metodos)
print("unitaria:", unitaria_metodos)
print("routing: ", routing_metodos)
