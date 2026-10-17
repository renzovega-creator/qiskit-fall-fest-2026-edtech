from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.circuit.library import CXGate, SwapGate
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import TransformationPass


class SwapACx(TransformationPass):
    def run(self, dag):
        for nodo in dag.op_nodes():
            if nodo.name != "swap":
                continue
            mini = DAGCircuit()
            reg = QuantumRegister(2)
            mini.add_qreg(reg)
            mini.apply_operation_back(SwapGate(), [reg[0], reg[1]])   # ✏️ cámbialo por tres CX
            dag.substitute_node_with_dag(nodo, mini)
        return dag


qc = QuantumCircuit(3)
qc.h(0)
qc.swap(0, 1)
qc.cx(1, 2)
qc.swap(1, 2)
print(dict(PassManager([SwapACx()]).run(qc).count_ops()))
