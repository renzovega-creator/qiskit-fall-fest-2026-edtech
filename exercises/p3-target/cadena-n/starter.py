from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def cadena(n):
    target = Target(f"cadena de {n}", num_qubits=n)
    target.add_instruction(RZGate(Parameter("t")), {(q,): None for q in range(n)})
    # ✏️ añade `sx`, `x` y `measure` en todos los qubits
    # ✏️ añade `cz` solo entre vecinos: (0, 1), (1, 2)…
    return target


print(sorted(cadena(4).operation_names))
