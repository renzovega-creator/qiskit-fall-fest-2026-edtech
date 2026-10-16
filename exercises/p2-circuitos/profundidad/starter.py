from qiskit import QuantumCircuit

qc = QuantumCircuit(3)
qc.h(0)
qc.x(1)
qc.cx(0, 1)
qc.z(2)
qc.h(1)

for inst in qc.data:
    print(inst.operation.name, [qc.find_bit(q).index for q in inst.qubits])

prediccion = None   # ✏️ tu apuesta: ¿cuánto vale qc.depth()? Compruébalo después con print(qc.depth())
