from qiskit import qasm2

programa_antiguo = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rxx(0.5) q[0], q[1];
"""

try:
    antiguo = qasm2.loads(programa_antiguo, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
except qasm2.QASM2ParseError as error:
    antiguo = None
    print("Error al importar:", str(error).splitlines()[0])

print(antiguo)
