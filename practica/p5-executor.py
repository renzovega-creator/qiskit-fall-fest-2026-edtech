import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.6 · Executor")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit.circuit import Parameter, QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import Executor
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    from qiskit_ibm_runtime.quantum_program import QuantumProgram
    from samplomatic import build
    from samplomatic.transpiler import generate_boxing_pass_manager

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeManilaV2()
    DISPAROS = 256
    rng = np.random.default_rng(3)

    # Un circuito GHZ de 3 qubits con dos parámetros: ideal, solo 000 y 111 (rz no cambia los conteos).
    circuito = QuantumCircuit(3)
    circuito.h(0)
    circuito.cx(0, 1)
    circuito.cx(1, 2)
    circuito.rz(Parameter("theta"), 0)
    circuito.rz(Parameter("phi"), 1)
    circuito.measure_all()

    pm = generate_preset_pass_manager(backend=backend, optimization_level=0)
    pm_cajas = generate_preset_pass_manager(backend=backend, optimization_level=0)
    pm_cajas.post_scheduling = generate_boxing_pass_manager(enable_gates=True, enable_measures=True)
    plantilla, samplex = build(pm_cajas.run(circuito))

    mo.md(f"""

    Tres misiones con `Executor` sobre `FakeManilaV2`, un procesador falso de 5 qubits. Cada
    programa usa {DISPAROS} disparos por configuración. No necesitas cuenta ni `Samplomatic`
    instalado aparte: ya viene en el entorno del curso.
    """)
    return (
        DISPAROS,
        Executor,
        QuantumProgram,
        backend,
        circuito,
        mo,
        np,
        plantilla,
        pm,
        rng,
        samplex,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un `CircuitItem` con 10 configuraciones

    Un `CircuitItem` ejecuta el circuito tal cual, sin aleatorizar, con 10 juegos de dos
    parámetros. Antes de ejecutar, predice la forma de `resultado[0]["meas"]`: los ejes de
    barrido a la izquierda, y los de disparos y bits a la derecha.
    """)
    return


@app.cell
def _(DISPAROS, Executor, QuantumProgram, backend, circuito, np, pm, rng):
    programa = QuantumProgram(shots=DISPAROS)
    programa.append_circuit_item(pm.run(circuito), circuit_arguments=rng.random((10, 2)))

    resultado = Executor(mode=backend).run(programa).result()
    forma = resultado[0]["meas"].shape
    forma
    return (forma,)


@app.cell(hide_code=True)
def _(DISPAROS, forma, veredicto):
    veredicto(forma == (10, DISPAROS, 3),
              f"La forma es {forma}: 10 configuraciones × {DISPAROS} disparos × 3 bits.",
              f"Salió {forma}; esperábamos (10, {DISPAROS}, 3).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: más aleatorizaciones

    Un `SamplexItem` genera variantes aleatorias (twirling) en el servidor. El parámetro
    `shape` añade ejes de aleatorización a la izquierda de los 10 juegos de parámetros:
    `shape=(2, 10)` pide **2** aleatorizaciones por configuración. Cámbialo para pedir **20**.
    """)
    return


@app.cell
def _(DISPAROS, Executor, QuantumProgram, backend, plantilla, rng, samplex):
    programa_twirl = QuantumProgram(shots=DISPAROS)
    programa_twirl.append_samplex_item(
        plantilla,
        samplex=samplex,
        samplex_arguments={"parameter_values": rng.random((10, 2))},
        shape=(2, 10),   # ✏️ (aleatorizaciones, configuraciones)
    )
    item = Executor(mode=backend).run(programa_twirl).result()[0]
    forma_twirl = item["meas"].shape
    forma_twirl
    return forma_twirl, item


@app.cell(hide_code=True)
def _(DISPAROS, forma_twirl, veredicto):
    veredicto(forma_twirl == (20, 10, DISPAROS, 3),
              f"La forma es {forma_twirl}: 20 aleatorizaciones × 10 configuraciones × {DISPAROS} disparos × 3 bits.",
              f"Salió {forma_twirl}; esperábamos (20, 10, {DISPAROS}, 3).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: deshacer el twirling de las mediciones

    Executor te devuelve los bits **tal como salieron**: el twirling de mediciones invirtió
    algunos al azar y anotó cuáles en `item["measurement_flips.meas"]`. Escribe
    `deshacer(item)`, que devuelva las mediciones corregidas con un XOR.

    La comprobación calcula qué fracción de disparos es `000` o `111`. El GHZ ideal da 100 %.
    """)
    return


@app.cell
def _():
    def deshacer(item):
        return item["meas"]   # ✏️ corrige las inversiones con measurement_flips.meas
    return (deshacer,)


@app.cell(hide_code=True)
def _(deshacer, item, np, veredicto):
    def _fraccion_ghz(bits):
        _suma = bits.sum(axis=-1)
        return float(np.mean((_suma == 0) | (_suma == bits.shape[-1])))

    _bits = deshacer(item)
    _antes = _fraccion_ghz(item["meas"])
    _despues = _fraccion_ghz(_bits)
    veredicto(_bits.shape == item["meas"].shape and _despues > _antes + 0.3,
              f"Antes del XOR, solo {_antes:.0%} de los disparos eran `000` o `111`; después, {_despues:.0%}.",
              f"Con tu función, {_despues:.0%} de los disparos son `000` o `111` (sin corregir: {_antes:.0%}). El XOR debería subirlo mucho.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `Sampler` deshace el twirling de mediciones por ti y `Executor` no. ¿Qué
    ganas a cambio de esa tarea extra?
    """)
    return


if __name__ == "__main__":
    app.run()
