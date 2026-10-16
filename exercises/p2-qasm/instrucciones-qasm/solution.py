from qiskit import qasm2

programa = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""
importado = qasm2.loads(programa)

prediccion = 4
print(len(importado.data), importado.count_ops())
