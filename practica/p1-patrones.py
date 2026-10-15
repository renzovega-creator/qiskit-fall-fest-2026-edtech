import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="1.2 · Patrones de Qiskit")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    backend = FakeBelemV2()

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def es_isa(isa):
        """Un circuito ISA usa solo puertas base y CNOT entre qubits vecinos del chip."""
        base = set(backend.operation_names)
        vecinos = {tuple(e) for e in backend.coupling_map.get_edges()}
        for inst in isa.data:
            if inst.operation.name not in base:
                return False
            if len(inst.qubits) == 2 and tuple(isa.find_bit(q).index for q in inst.qubits) not in vecinos:
                return False
        return True

    mo.md("""
    # 1.2 · El flujo de trabajo: práctica

    Tres misiones sobre los cuatro pasos de un patrón: mapear, optimizar, ejecutar y
    posprocesar. Usan un backend falso de cinco qubits (`FakeBelemV2`) y el simulador exacto,
    así que no necesitan cuenta ni red. Busca el ✅.
    """)
    return (
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        StatevectorEstimator,
        backend,
        es_isa,
        generate_preset_pass_manager,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: los cuatro pasos

    El programa de la lección, con el simulador exacto en el paso 3. El valor ideal de
    $\\langle ZZ\\rangle+\\langle XX\\rangle$ en un estado de Bell es 2. Lee cada paso y comprueba
    que el circuito ISA solo usa las puertas base del backend.
    """)
    return


@app.cell
def _(
    QuantumCircuit,
    SparsePauliOp,
    StatevectorEstimator,
    backend,
    generate_preset_pass_manager,
):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    obs = SparsePauliOp(["ZZ", "XX"])

    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa = pm.run(qc)
    isa_obs = obs.apply_layout(isa.layout)

    resultado = StatevectorEstimator().run([(isa, isa_obs)]).result()

    valor = float(resultado[0].data.evs)
    valor, dict(isa.count_ops())
    return isa, qc, valor


@app.cell(hide_code=True)
def _(es_isa, isa, valor, veredicto):
    veredicto(
        abs(valor - 2) < 1e-6 and es_isa(isa),
        "Valor ideal 2, con un circuito ISA: puertas base y conectividad del chip.",
        "Deberías obtener 2 con un circuito ISA. ¿Cambiaste algún paso?",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: otro observable

    Añade `"YY"` al observable. **Antes de ejecutar, apuesta:** para el estado de Bell,
    $\\langle ZZ\\rangle=\\langle XX\\rangle=1$. ¿Cuánto vale $\\langle YY\\rangle$, y cuánto
    la suma de los tres? (El signo no es obvio: mira la comprobación si dudas.)
    """)
    return


@app.cell
def _(SparsePauliOp, StatevectorEstimator, isa):
    obs_3 = SparsePauliOp(["ZZ", "XX"])  # ✏️ añade "YY"
    valor_3 = float(StatevectorEstimator().run([(isa, obs_3.apply_layout(isa.layout))]).result()[0].data.evs)
    valor_3
    return obs_3, valor_3


@app.cell(hide_code=True)
def _(obs_3, valor_3, veredicto):
    veredicto(
        len(obs_3) == 3 and abs(valor_3 - 1) < 1e-6,
        "$\\langle ZZ\\rangle+\\langle XX\\rangle+\\langle YY\\rangle = 1+1-1 = 1$: en el estado de Bell, $YY$ vale $-1$.",
        f"Ahora la suma da {valor_3:.3f} con {len(obs_3)} términos. Debe tener tres: ZZ, XX y YY.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el patrón como función

    Escribe `patron(qc, obs, backend, nivel)`: hace los pasos 2, 3 y 4 y devuelve
    `(isa, valor)`: el circuito ISA y el valor esperado ideal. La comprobación la prueba con
    un GHZ de tres qubits y los niveles de optimización 0, 1 y 3.
    """)
    return


@app.cell
def _(StatevectorEstimator, generate_preset_pass_manager):
    def patron(qc, obs, backend, nivel=1):
        """Optimiza, ejecuta y posprocesa. Devuelve (circuito ISA, valor esperado)."""
        # ✏️ 2. Optimizar: pass manager del backend, circuito ISA y observable con su layout
        # ✏️ 3. Ejecutar: StatevectorEstimator sobre (isa, observable)
        # ✏️ 4. Posprocesar: devuelve el valor como float
        return qc, 0.0
    return (patron,)


@app.cell(hide_code=True)
def _(QuantumCircuit, SparsePauliOp, Statevector, backend, es_isa, patron, veredicto):
    def _ok():
        ghz = QuantumCircuit(3)
        ghz.h(0)
        ghz.cx(0, 1)
        ghz.cx(1, 2)
        obs = SparsePauliOp(["ZZI", "IZZ", "XXX"])
        ideal = Statevector(ghz).expectation_value(obs).real
        for nivel in (0, 1, 3):
            isa, valor = patron(ghz, obs, backend, nivel)
            if not es_isa(isa) or abs(valor - ideal) > 1e-6:
                return False
        return True

    veredicto(
        _ok(),
        "Tu `patron` devuelve circuitos ISA y el valor ideal 3 para GHZ en los niveles 0, 1 y 3.",
        "Falla algún nivel: el circuito no es ISA o el valor no es 3. ¿Aplicaste el layout al observable?",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** los tres niveles dan el mismo valor ideal, pero circuitos distintos.
    Compara `isa.count_ops()` y `isa.depth()` entre niveles. En hardware real, ¿cuál
    esperas que dé un valor más cercano al ideal?
    """)
    return


if __name__ == "__main__":
    app.run()
