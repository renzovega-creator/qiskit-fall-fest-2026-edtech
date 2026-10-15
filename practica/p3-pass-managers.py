import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.5 · Pass managers y desacoplamiento dinámico")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import TdgGate, TGate, XGate
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.quantum_info import Operator
    from qiskit.transpiler import PassManager, generate_preset_pass_manager
    from qiskit.transpiler.passes import (
        Collect2qBlocks,
        ConsolidateBlocks,
        InverseCancellation,
        UnitarySynthesis,
    )
    from qiskit.transpiler.passes.scheduling import ALAPScheduleAnalysis, PadDynamicalDecoupling
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 3.5 · Pass managers y desacoplamiento dinámico: práctica

    Tres misiones: armar un pass manager con tus pases, meter un pase en una etapa de uno
    prediseñado y construir el pass manager de desacoplamiento dinámico.
    """)
    return (
        ALAPScheduleAnalysis,
        Collect2qBlocks,
        ConsolidateBlocks,
        FakeFez,
        GenericBackendV2,
        InverseCancellation,
        Operator,
        PadDynamicalDecoupling,
        PassManager,
        QuantumCircuit,
        TGate,
        TdgGate,
        UnitarySynthesis,
        XGate,
        generate_preset_pass_manager,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un pass manager propio

    Tres pases en fila: junta las puertas de dos qubits en bloques, los consolida en una unitaria
    y la sintetiza con las puertas `rx`, `ry` y `rxx`. Antes de ejecutar, predice qué puertas
    quedan al aplicarlo a una Hadamard seguida de dos CX.
    """)
    return


@app.cell
def _(Collect2qBlocks, ConsolidateBlocks, PassManager, QuantumCircuit, UnitarySynthesis):
    puertas_iones = ["rx", "ry", "rxx"]
    traducir = PassManager([
        Collect2qBlocks(),
        ConsolidateBlocks(basis_gates=puertas_iones),
        UnitarySynthesis(puertas_iones),
    ])
    circuito_hcx = QuantumCircuit(2)
    circuito_hcx.h(0)
    circuito_hcx.cx(0, 1)
    circuito_hcx.cx(1, 0)
    puertas_traducidas = sorted(traducir.run(circuito_hcx).count_ops())
    puertas_traducidas
    return (puertas_traducidas,)


@app.cell(hide_code=True)
def _(puertas_traducidas, veredicto):
    veredicto(puertas_traducidas == ["rx", "rxx", "ry"],
              "El circuito solo contiene `rx`, `rxx` y `ry`: las de un computador de iones atrapados.",
              f"Salieron {puertas_traducidas}; deberían ser solo `rx`, `rxx` y `ry`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un pase en la etapa `pre_layout`

    El circuito tiene dos pares `T`, `T†` seguidos, que se anulan. Con el nivel 0 el transpilador
    no los cancela y los traduce a rotaciones `rz`. Asigna a `pm_nivel0.pre_layout` un `PassManager`
    con `InverseCancellation([(TGate(), TdgGate())])` para que el resultado sea idéntico al del
    circuito sin esos pares.
    """)
    return


@app.cell
def _(FakeFez, InverseCancellation, PassManager, QuantumCircuit, TGate, TdgGate, generate_preset_pass_manager):
    con_pares = QuantumCircuit(2)
    con_pares.h(0)
    con_pares.t(0)
    con_pares.tdg(0)
    con_pares.cx(0, 1)
    con_pares.t(1)
    con_pares.tdg(1)
    con_pares.h(1)

    sin_pares = QuantumCircuit(2)
    sin_pares.h(0)
    sin_pares.cx(0, 1)
    sin_pares.h(1)

    fez = FakeFez()
    pm_nivel0 = generate_preset_pass_manager(0, backend=fez, seed_transpiler=1)
    # ✏️ asigna pm_nivel0.pre_layout

    puertas_con = dict(pm_nivel0.run(con_pares).count_ops())
    puertas_ref = dict(generate_preset_pass_manager(0, backend=fez, seed_transpiler=1).run(sin_pares).count_ops())
    puertas_con
    return puertas_con, puertas_ref


@app.cell(hide_code=True)
def _(puertas_con, puertas_ref, veredicto):
    veredicto(puertas_con == puertas_ref,
              f"Ahora el circuito con los pares da lo mismo que el que no los tiene: {puertas_ref}.",
              f"Salen {puertas_con}; sin los pares sería {puertas_ref}. ¿Asignaste `pre_layout` con `InverseCancellation`?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el pass manager de desacoplamiento dinámico

    El circuito ya está transpilado y con los tiempos calculados (por eso hay instrucciones `delay`).
    Rellena `dd_pm` con **dos pases**, en este orden: `ALAPScheduleAnalysis(target=...)` y
    `PadDynamicalDecoupling(target=..., dd_sequence=[XGate(), XGate()])`.
    La comprobación exige que aparezcan puertas `x` en las esperas y que el operador no cambie.
    """)
    return


@app.cell
def _(ALAPScheduleAnalysis, GenericBackendV2, PadDynamicalDecoupling, PassManager, QuantumCircuit, XGate, generate_preset_pass_manager):
    backend5 = GenericBackendV2(5, seed=1)
    objetivo = backend5.target

    ghz5 = QuantumCircuit(5)
    ghz5.h(0)
    ghz5.cx(0, range(1, 5))
    programado = generate_preset_pass_manager(
        1, backend=backend5, scheduling_method="asap", seed_transpiler=1234).run(ghz5)

    dd_pm = PassManager([
        # ✏️ análisis de tiempos y relleno con la secuencia X, X
    ])
    con_dd = dd_pm.run(programado)
    print("x antes:", programado.count_ops().get("x", 0), "· x después:", con_dd.count_ops().get("x", 0))
    return con_dd, programado


@app.cell(hide_code=True)
def _(Operator, con_dd, programado, veredicto):
    _antes, _despues = programado.count_ops().get("x", 0), con_dd.count_ops().get("x", 0)
    veredicto(_despues > _antes and Operator(con_dd).equiv(Operator(programado)),
              f"Tu pass manager añadió {_despues - _antes} puertas X en las esperas, y el operador es el mismo: el desacoplamiento no cambia el cálculo.",
              "No se añadieron puertas X, o el operador cambió. Necesitas el análisis de tiempos y luego el relleno.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿por qué el análisis de tiempos tiene que ir **antes** del relleno?
    En el hito III verás cuánta profundidad añaden los pasos de Trotter; ¿qué pase pondrías tú en `pre_layout`?
    """)
    return


if __name__ == "__main__":
    app.run()
