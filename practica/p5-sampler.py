import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.5 · Sampler en IBM Quantum")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    def sampler_local(shots=4000):
        s = Sampler(mode=backend)
        s.options.default_shots = shots
        s.options.simulator.seed_simulator = 11
        return s

    def ghz_medido(n):
        if not 2 <= n <= backend.num_qubits:
            raise ValueError(f"n debe estar entre 2 y {backend.num_qubits}, los qubits de {backend.name}")
        qc = QuantumCircuit(n)
        qc.h(0)
        for i in range(n - 1):
            qc.cx(i, i + 1)
        qc.measure_all()
        return qc

    mo.md("""

    Tres misiones con `Sampler` sobre `FakeManilaV2`, un procesador falso de 5 qubits. No
    necesitas cuenta. Busca el ✅ en cada misión.
    """)
    return ghz_medido, mo, plt, pm, sampler_local, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un GHZ de 5 qubits con ruido

    Idealmente solo saldrían `00000` y `11111`. Antes de ejecutar, predice: ¿qué fracción de
    los 4000 disparos crees que **no** será ninguna de las dos? ¿1 %, 20 %, 60 %?
    """)
    return


@app.cell
def _(ghz_medido, pm, sampler_local):
    isa = pm.run(ghz_medido(5))
    conteos = sampler_local(4000).run([isa]).result()[0].data.meas.get_counts()

    ideales = conteos.get("00000", 0) + conteos.get("11111", 0)
    fraccion_ruido = 1 - ideales / sum(conteos.values())
    print(f"{ideales} de {sum(conteos.values())} disparos son 00000 o 11111 → {fraccion_ruido:.1%} con algún bit cambiado")
    dict(sorted(conteos.items(), key=lambda kv: -kv[1])[:6])
    return conteos, fraccion_ruido, isa


@app.cell(hide_code=True)
def _(conteos, fraccion_ruido, veredicto):
    veredicto(sum(conteos.values()) == 4000 and 0.02 < fraccion_ruido < 0.6,
              f"{fraccion_ruido:.1%} de los disparos tiene algún bit cambiado por el ruido.",
              "Deberían ser 4000 disparos, con una fracción de ruido entre el 2 % y el 60 %.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un solo número de disparos por trabajo

    Con el `Sampler` de la 0.50, todos los PUBs de un trabajo deben tener **el mismo** número
    de disparos. Esta celda pide 64 para uno y 128 para otro en el mismo `run` y falla.
    Consérvalos: reparte los PUBs en **dos trabajos**, uno por número de disparos.
    """)
    return


@app.cell
def _(isa, sampler_local):
    sampler = sampler_local()
    try:
        resultado = sampler.run([(isa, None, 64), (isa, None, 128)]).result()   # ✏️ un trabajo por número de disparos
        disparos = [pub.data.meas.num_shots for pub in resultado]
    except Exception as error:
        disparos = []
        print("Error:", error)
    disparos
    return (disparos,)


@app.cell(hide_code=True)
def _(disparos, veredicto):
    veredicto(disparos == [64, 128],
              "Cada trabajo respeta su propio número de disparos: 64 y 128.",
              f"Salió {disparos}. Debe quedar [64, 128], con un trabajo por cada número.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: cómo crece el ruido con el tamaño

    1. Escribe `fraccion_errores(conteos)`: la fracción de disparos que **no** es todo ceros ni
       todo unos. Las cadenas tienen todas la misma longitud.
    2. La celda de abajo la aplica a GHZ de 2 a 5 qubits y los grafica: ¿crece con $n$?
    """)
    return


@app.cell
def _():
    def fraccion_errores(conteos):
        return 0.0   # ✏️ disparos que no son todo 0 ni todo 1, entre el total
    return (fraccion_errores,)


@app.cell(hide_code=True)
def _(fraccion_errores, ghz_medido, pm, sampler_local):
    tamanos = [2, 3, 4, 5]
    errores = []
    for _n in tamanos:
        _c = sampler_local(4000).run([pm.run(ghz_medido(_n))]).result()[0].data.meas.get_counts()
        errores.append(fraccion_errores(_c))
    return errores, tamanos


@app.cell(hide_code=True)
def _(errores, fraccion_errores, veredicto):
    _manual = fraccion_errores({"000": 50, "111": 30, "001": 15, "110": 5})
    _limpio = fraccion_errores({"00": 10, "11": 10})
    veredicto(abs(_manual - 0.2) < 1e-9 and _limpio == 0 and errores[-1] > errores[0],
              f"Tu función funciona y el ruido crece con el tamaño: {errores[0]:.1%} con 2 qubits, {errores[-1]:.1%} con 5.",
              "Prueba a mano: `{'000': 50, '111': 30, '001': 15, '110': 5}` debe dar 0.2 y un conteo limpio, 0.")
    return


@app.cell(hide_code=True)
def _(errores, plt, tamanos):
    _fig, _ax = plt.subplots(figsize=(5, 2.6))
    _ax.plot(tamanos, errores, "o-")
    _ax.set_xticks(tamanos)
    _ax.set_xlabel("qubits del GHZ")
    _ax.set_ylabel("fracción con errores")
    _ax.set_ylim(0, 0.5)
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** cada qubit más añade una CNOT y una medición. ¿Cuál de las dos crees que
    aporta más errores? ¿Qué opción de `Sampler` probarías para saberlo?
    """)
    return


if __name__ == "__main__":
    app.run()
