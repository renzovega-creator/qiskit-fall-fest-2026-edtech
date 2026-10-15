import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="1.1 · Qué es Qiskit")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import CXGate, HGate
    from qiskit.primitives import StatevectorEstimator, StatevectorSampler
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 1.1 · Qué es Qiskit: práctica

    Tres misiones, de menos a más. Cada una tiene una comprobación que se actualiza sola
    al cambiar el código: busca el ✅. Todo corre en tu equipo, sin cuenta de IBM.
    """)
    return (
        CXGate,
        CouplingMap,
        HGate,
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        StatevectorEstimator,
        StatevectorSampler,
        generate_preset_pass_manager,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: las piezas del SDK en un solo programa

    Un estado de Bell pasa por cuatro módulos del SDK. Cada línea dice de cuál es.
    No tienes que cambiar nada: ejecuta y lee los resultados.
    """)
    return


@app.cell
def _(
    CXGate,
    CouplingMap,
    HGate,
    QuantumCircuit,
    Statevector,
    StatevectorSampler,
    generate_preset_pass_manager,
):
    bell = QuantumCircuit(2)  # qiskit.circuit
    bell.append(HGate(), [0])  # qiskit.circuit.library
    bell.append(CXGate(), [0, 1])

    exacto = Statevector(bell).probabilities_dict()  # qiskit.quantum_info: exacto, sin muestreo

    medido = bell.measure_all(inplace=False)
    pm = generate_preset_pass_manager(  # qiskit.transpiler
        optimization_level=1, basis_gates=["rz", "sx", "cz"], coupling_map=CouplingMap.from_line(2)
    )
    isa = pm.run(medido)

    muestras = StatevectorSampler(seed=7).run([isa], shots=1024).result()[0].data.meas.get_counts()  # qiskit.primitives
    exacto, muestras, dict(isa.count_ops())
    return exacto, isa, muestras


@app.cell(hide_code=True)
def _(exacto, isa, muestras, veredicto):
    veredicto(
        set(muestras) == {"00", "11"}
        and all(abs(p - 0.5) < 1e-9 for p in exacto.values())
        and set(isa.count_ops()) <= {"rz", "sx", "cz", "measure", "barrier"},
        "El cálculo exacto da 1/2 y 1/2, las muestras solo `00` y `11`, y el circuito transpilado usa solo puertas base.",
        "Deberían salir solo `00` y `11`, con probabilidad exacta 1/2 cada una. ¿Cambiaste algo del circuito?",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un observable exacto

    `qiskit.quantum_info` calcula valores esperados **sin simular mediciones**. Ahora mide
    $\\langle ZZ\\rangle$ en el estado de Bell: vale 1.

    Cambia `obs` para medir solo la $Z$ del qubit 0. **Antes de ejecutar, apuesta:** ¿0 o 1?
    (En Qiskit el qubit 0 es el que está más a la derecha de la etiqueta.)
    """)
    return


@app.cell
def _(SparsePauliOp, Statevector, bell):
    obs = SparsePauliOp("ZZ")  # ✏️ cambia el observable
    valor = Statevector(bell).expectation_value(obs).real
    valor
    return obs, valor


@app.cell(hide_code=True)
def _(obs, valor, veredicto):
    veredicto(
        abs(valor) < 1e-9 and obs.num_qubits == 2 and set(obs.paulis.to_labels()) == {"IZ"},
        "Un solo qubit del estado de Bell es una moneda perfecta: $\\langle Z_0\\rangle = 0$.",
        f"Ahora el valor es {valor:.3f}. Mide solo la Z del qubit 0 sobre un observable de dos qubits.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: tu propio valor esperado

    Escribe `valor_esperado(qc, obs)`: devuelve el valor esperado **exacto** de `obs` en el
    estado que prepara `qc` (sin mediciones), usando solo `qiskit.quantum_info`.
    La comprobación lo compara con `StatevectorEstimator`, la primitiva que hace lo mismo.
    """)
    return


@app.cell
def _(Statevector):
    def valor_esperado(qc, obs):
        """Valor esperado exacto de `obs` en el estado que prepara `qc`."""
        # ✏️ usa Statevector y expectation_value
        return 0.0
    return (valor_esperado,)


@app.cell(hide_code=True)
def _(QuantumCircuit, SparsePauliOp, StatevectorEstimator, valor_esperado, veredicto):
    def _circuitos():
        bell = QuantumCircuit(2)
        bell.h(0)
        bell.cx(0, 1)
        ghz = QuantumCircuit(3)
        ghz.h(0)
        ghz.cx(0, 1)
        ghz.cx(1, 2)
        ry = QuantumCircuit(2)
        ry.ry(0.7, 0)
        ry.cx(0, 1)
        return [(bell, "ZZ"), (bell, "XX"), (bell, "YY"), (bell, "IZ"), (ghz, "XXX"), (ghz, "IZZ"), (ry, "IZ")]

    def _ok():
        for qc, etiqueta in _circuitos():
            obs = SparsePauliOp(etiqueta)
            esperado = StatevectorEstimator().run([(qc, obs)]).result()[0].data.evs
            if abs(valor_esperado(qc, obs) - esperado) > 1e-9:
                return False
        return True

    veredicto(
        _ok(),
        "Tu `valor_esperado` coincide con `StatevectorEstimator` en siete casos de 2 y 3 qubits.",
        "Algún caso no coincide con `StatevectorEstimator`. ¿Devuelves un número real, no complejo?",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si `quantum_info` ya da el valor exacto, ¿para qué sirven las primitivas
    y el servicio de IBM? Piensa en qué pasa con 100 qubits.
    """)
    return


if __name__ == "__main__":
    app.run()
