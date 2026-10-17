from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CCXGate, HGate
from qiskit.converters import circuit_to_dag, dag_to_circuit


def envolver(circuito):
    dag = circuit_to_dag(circuito)
    # ✏️ añade una H al final sobre el qubit 0 y una Toffoli al principio sobre los qubits 0, 1 y 2
    return dag_to_circuit(dag)


q = QuantumRegister(3, "q")
c = ClassicalRegister(3, "c")
circ = QuantumCircuit(q, c)
circ.h(q[0])
circ.cx(q[0], q[1])
circ.measure(q[0], c[0])
with circ.if_test((c, 2)):
    circ.rz(0.5, q[1])
print(dict(envolver(circ).count_ops()))
