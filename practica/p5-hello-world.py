import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.2 · Hola mundo en un QPU")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Un backend falso de 5 qubits: corre en tu equipo con el ruido de un dispositivo real.
    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    def estimator_local(shots, nivel=1):
        est = Estimator(mode=backend)
        est.options.resilience_level = nivel
        est.options.default_shots = shots
        est.options.simulator.seed_simulator = 7
        return est

    mo.md("""

    Los cuatro pasos de la lección (mapear, optimizar, ejecutar, posprocesar) sobre un
    **backend falso**: `FakeManilaV2` simula el ruido de un procesador de 5 qubits. No
    necesitas cuenta; el código es el mismo que enviarías a hardware real.
    """)
    return (
        QiskitRuntimeService,
        QuantumCircuit,
        SparsePauliOp,
        backend,
        estimator_local,
        mo,
        plt,
        pm,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el estado de Bell con Estimator

    Antes de ejecutar, apunta tu apuesta: de estos seis observables, ¿cuáles valdrán casi 1
    y cuáles casi 0? Luego ejecuta y compara.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, estimator_local, pm):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)

    etiquetas = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
    isa_bell = pm.run(bell)
    mapeados = [SparsePauliOp(e).apply_layout(isa_bell.layout) for e in etiquetas]

    resultado = estimator_local(5000).run([(isa_bell, mapeados)]).result()[0]
    valores = dict(zip(etiquetas, resultado.data.evs.round(2).tolist()))
    valores
    return (valores,)


@app.cell(hide_code=True)
def _(valores, veredicto):
    veredicto(valores["ZZ"] > 0.8 and valores["XX"] > 0.8 and all(abs(valores[k]) < 0.15 for k in ("IZ", "IX", "ZI", "XI")),
              "Cada qubit por separado vale ≈ 0 y las correlaciones `ZZ` y `XX` valen ≈ 1: la firma del entrelazamiento.",
              f"Esperábamos qubits sueltos ≈ 0 y `ZZ`, `XX` ≈ 1; salió {valores}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: más disparos, menos error

    `stds` es la desviación estándar del valor esperado y baja como $1/\\sqrt{\\text{disparos}}$.
    Cambia **solo** `default_shots` para que el error de $\\langle ZZ\\rangle$ quede por debajo de
    $0{,}004$. En hardware, cada disparo extra es tiempo de QPU: busca el menor valor que baste.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, estimator_local, pm):
    _bell = QuantumCircuit(2)
    _bell.h(0)
    _bell.cx(0, 1)
    _isa = pm.run(_bell)

    disparos = 1000   # ✏️ prueba otros valores
    _res = estimator_local(disparos).run([(_isa, SparsePauliOp("ZZ").apply_layout(_isa.layout))]).result()[0]
    error_zz = float(_res.data.stds)
    f"{disparos} disparos → ⟨ZZ⟩ = {float(_res.data.evs):.3f} ± {error_zz:.4f}"
    return disparos, error_zz


@app.cell(hide_code=True)
def _(disparos, error_zz, veredicto):
    veredicto(error_zz < 0.004,
              f"Con {disparos} disparos el error es {error_zz:.4f}. Cuatro veces más disparos, la mitad de error.",
              f"Con {disparos} disparos el error es {error_zz:.4f}; todavía no baja de 0,004.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el GHZ y el decaimiento por ruido

    Escribe `correlaciones(n)`: prepara un GHZ de `n` qubits, de 2 a 5 (los que caben en
    `FakeManilaV2`; con más, la función avisa con un error), con una $H$ y una cadena de CNOT, y
    devuelve la lista de $\\langle Z_0 Z_i\\rangle$ para $i = 1 \\dots n-1$. Con Qiskit, el qubit 0
    va a la **derecha** de la cadena de Pauli: $Z_0Z_2$ en 4 qubits es `"IZIZ"`.

    Idealmente todas valen 1. Mueve el control de $n$ y mira cuánto se aleja el ruido de ese ideal.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, backend, estimator_local, pm):
    def correlaciones(n):
        if not 2 <= n <= backend.num_qubits:
            raise ValueError(f"n debe estar entre 2 y {backend.num_qubits}, los qubits de {backend.name}")
        ghz = QuantumCircuit(n)
        # ✏️ H en el qubit 0 y una cadena de CNOT
        isa = pm.run(ghz)
        etiquetas = ["I" * n]   # ✏️ una cadena de Pauli por cada i = 1…n-1, con Z en los qubits 0 e i
        ops = [SparsePauliOp(e).apply_layout(isa.layout) for e in etiquetas]
        evs = estimator_local(4000).run([(isa, ops)]).result()[0].data.evs
        return [round(float(v), 3) for v in evs]
    return (correlaciones,)


@app.cell(hide_code=True)
def _(correlaciones, veredicto):
    _c = correlaciones(5)
    veredicto(len(_c) == 4 and all(0.6 < v < 1.05 for v in _c),
              f"⟨Z₀Zᵢ⟩ = {_c}: cuatro correlaciones cerca de 1, un poco por debajo del valor ideal.",
              f"Para n = 5 esperábamos 4 valores cercanos a 1 (el ideal); salió {_c}.")
    return


@app.cell(hide_code=True)
def _(mo):
    n_slider = mo.ui.slider(2, 5, value=5, label="qubits del GHZ", show_value=True)
    n_slider
    return (n_slider,)


@app.cell(hide_code=True)
def _(correlaciones, n_slider, plt):
    _c = correlaciones(n_slider.value)
    _fig, _ax = plt.subplots(figsize=(5, 2.6))
    _ax.axhline(1, color="gray", ls="--", lw=1)
    _ax.plot(range(1, len(_c) + 1), _c, "o-")
    _ax.set_ylim(0, 1.1)
    _ax.set_xlabel("distancia i")
    _ax.set_ylabel("⟨Z₀Zᵢ⟩")
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    ver_qpu = mo.ui.switch(label="Ver qué procesador elegiría `least_busy` (opcional · consulta de red, no envía nada)")
    mo.vstack([
        mo.md("""
        ---
        ### Opcional: el procesador menos ocupado

        Este cuaderno **nunca envía trabajos**. Si tienes una cuenta guardada, el interruptor
        solo pregunta cuál sería el procesador real menos ocupado. Sin cuenta, no hace nada.
        El primer envío real es el hito V del proyecto.
        """),
        ver_qpu,
    ])
    return (ver_qpu,)


@app.cell(hide_code=True)
def _(QiskitRuntimeService, mo, ver_qpu):
    mo.stop(not ver_qpu.value, mo.md("_Apagado: se usa el backend falso._"))
    mo.stop(not QiskitRuntimeService.saved_accounts(),
            mo.md("_No hay credenciales guardadas: nada que consultar._"))
    from qiskit.exceptions import QiskitError

    try:
        _elegido = QiskitRuntimeService().least_busy(simulator=False, operational=True)
    except (QiskitError, OSError) as _e:
        mo.stop(True, mo.md(f"No se pudo consultar el servicio ({type(_e).__name__}): no se muestra nada."))
    mo.md(f"`least_busy` elegiría **{_elegido.name}** ({_elegido.num_qubits} qubits).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué crees que pasaría con $\\langle Z_0Z_i\\rangle$ si el GHZ tuviera 100
    qubits? ¿Qué parte del circuito sería la culpable?
    """)
    return


if __name__ == "__main__":
    app.run()
