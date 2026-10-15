import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.6 · Escribir pases propios: el DAG")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from qiskit.circuit.library import CCXGate, CXGate, HGate, SwapGate
    from qiskit.converters import circuit_to_dag, dag_to_circuit
    from qiskit.dagcircuit import DAGCircuit
    from qiskit.quantum_info import Operator
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.basepasses import AnalysisPass, TransformationPass

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 3.6 · Escribir pases propios: práctica

    Tres misiones: recorrer un DAG, escribir un pase de transformación y escribir un pase de análisis.
    Los pases se prueban sobre circuitos pequeños, sin backend.
    """)
    return (
        AnalysisPass,
        CCXGate,
        CXGate,
        ClassicalRegister,
        DAGCircuit,
        HGate,
        Operator,
        PassManager,
        QuantumCircuit,
        QuantumRegister,
        SwapGate,
        TransformationPass,
        circuit_to_dag,
        dag_to_circuit,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: operaciones con el DAG

    Convierte un circuito en DAG, añade una `H` al final y una Toffoli al principio, y vuelve al circuito.
    Antes de ejecutar, predice cuántas `h` tendrá el resultado.
    """)
    return


@app.cell
def _(CCXGate, ClassicalRegister, HGate, QuantumCircuit, QuantumRegister, circuit_to_dag, dag_to_circuit):
    q = QuantumRegister(3, "q")
    c = ClassicalRegister(3, "c")
    circ = QuantumCircuit(q, c)
    circ.h(q[0])
    circ.cx(q[0], q[1])
    circ.measure(q[0], c[0])
    with circ.if_test((c, 2)):
        circ.rz(0.5, q[1])

    dag = circuit_to_dag(circ)
    print([node.name for node in dag.op_nodes()])
    dag.apply_operation_back(HGate(), qargs=[q[0]])
    dag.apply_operation_front(CCXGate(), qargs=[q[0], q[1], q[2]])
    ops_finales = dict(dag_to_circuit(dag).count_ops())
    ops_finales
    return (ops_finales,)


@app.cell(hide_code=True)
def _(ops_finales, veredicto):
    veredicto(ops_finales.get("h") == 2 and ops_finales.get("ccx") == 1,
              f"El resultado tiene {ops_finales['h']} `h` (la original y la que añadiste) y 1 `ccx` al principio.",
              f"Salió {ops_finales}. Deberían ser 2 `h` y 1 `ccx`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un pase que traduce los SWAP

    Este `TransformationPass` sustituye cada `swap` por un mini DAG... que contiene otro `swap`.
    Cámbialo para que el mini DAG tenga **tres CX**: (0, 1), (1, 0) y (0, 1).
    La comprobación exige el mismo operador y ningún `swap`.
    """)
    return


@app.cell
def _(DAGCircuit, QuantumRegister, SwapGate, TransformationPass):
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
    return (SwapACx,)


@app.cell(hide_code=True)
def _(Operator, PassManager, QuantumCircuit, SwapACx, veredicto):
    _qc = QuantumCircuit(3)
    _qc.h(0)
    _qc.swap(0, 1)
    _qc.cx(1, 2)
    _qc.swap(1, 2)
    _out = PassManager([SwapACx()]).run(_qc)
    _ops = dict(_out.count_ops())
    veredicto("swap" not in _ops and _ops.get("cx") == 7 and Operator(_out).equiv(_qc),
              "Cada SWAP se convirtió en tres CX, y el circuito sigue haciendo lo mismo: 1 CX + 2 × 3 = 7.",
              f"Salió {_ops}. Debe quedar sin `swap`, con 7 `cx` y el mismo operador.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un pase de análisis

    Escribe `ContarDosQubits`, un `AnalysisPass` que **cuente** las puertas de dos qubits del DAG
    y guarde el número en `self.property_set["n2q"]`, sin tocar el DAG.
    Pista: `dag.two_qubit_ops()` devuelve las operaciones de exactamente dos qubits.
    """)
    return


@app.cell
def _(AnalysisPass):
    class ContarDosQubits(AnalysisPass):
        def run(self, dag):
            pass  # ✏️ cuenta las puertas de dos qubits y guárdalas en self.property_set["n2q"]
    return (ContarDosQubits,)


@app.cell(hide_code=True)
def _(ContarDosQubits, QuantumCircuit, circuit_to_dag, dag_to_circuit, veredicto):
    _a = QuantumCircuit(3)
    _a.h(0)
    _a.cx(0, 1)
    _a.cz(1, 2)
    _a.swap(0, 2)
    _b = QuantumCircuit(2)
    _b.h(0)
    _b.x(1)
    _c = QuantumCircuit(3)
    _c.ccx(0, 1, 2)
    _c.cx(0, 1)
    _malos = []
    for _qc, _esperado in ((_a, 3), (_b, 0), (_c, 1)):
        _dag = circuit_to_dag(_qc)
        _pase = ContarDosQubits()
        _pase.run(_dag)
        if _pase.property_set.get("n2q") != _esperado or dag_to_circuit(_dag) != _qc:
            _malos.append((_esperado, _pase.property_set.get("n2q")))
    veredicto(not _malos,
              "Tu pase cuenta 3, 0 y 1 puertas de dos qubits en los circuitos de prueba, y deja el DAG igual.",
              f"Falló en {len(_malos)} de 3 circuitos (esperado, obtenido): {_malos}. Recuerda escribir también el 0, y que una Toffoli no es de dos qubits.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué pase de análisis te ayudaría a decidir cuántos pasos de Trotter caben en tu proyecto Ising?
    En el hito III medirás la profundidad con el transpilador completo.
    """)
    return


if __name__ == "__main__":
    app.run()
