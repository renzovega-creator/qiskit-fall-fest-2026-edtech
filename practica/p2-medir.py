import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.2 · Medir qubits")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.primitives import StatevectorSampler, StatevectorEstimator

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.2 · Medir qubits: práctica

    Tres misiones sobre dónde va cada resultado: los registros clásicos de `measure_all`,
    el emparejamiento de `measure` y la regla de Sampler con mediciones, Estimator sin ellas.
    """)
    return QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: `measure_all` crea un registro nuevo

    Este circuito ya tenía 1 bit clásico. Antes de ejecutar la celda, escribe en `prediccion`
    cuántos bits clásicos tendrá **después** de `measure_all()`.
    """)
    return


@app.cell
def _(QuantumCircuit, StatevectorSampler):
    qc = QuantumCircuit(3, 1)
    qc.x([0, 2])
    qc.measure_all()

    prediccion = None   # ✏️ tu apuesta: ¿cuántos bits clásicos?

    conteos = StatevectorSampler(seed=7).run([qc], shots=256).result()[0].data.meas.get_counts()
    print("bits clásicos:", qc.num_clbits, "· conteos de meas:", conteos)
    return prediccion, qc


@app.cell(hide_code=True)
def _(prediccion, qc, veredicto):
    veredicto(prediccion == qc.num_clbits,
              f"Acertaste: {qc.num_clbits} bits. El registro `c` original sigue ahí y `meas` trae uno por qubit.",
              f"Tu apuesta ({prediccion}) no coincide con los {qc.num_clbits} bits del circuito. "
              "Recuerda: `measure_all` no reutiliza `c`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: qué qubit va a qué bit

    El qubit 2 vale 1 y los otros valen 0. Quieres que el resultado, escrito como cadena
    `'c1c0'`, sea `'01'`: el **qubit 2** debe guardarse en el **bit 0**, y el qubit 0 en el bit 1.
    Cambia los argumentos de `measure`.
    """)
    return


@app.cell
def _(QuantumCircuit, StatevectorSampler):
    emparejado = QuantumCircuit(3, 2)
    emparejado.x(2)
    emparejado.measure([0, 2], [0, 1])   # ✏️ qubits y bits en el orden que pide el enunciado

    conteos_emparejado = StatevectorSampler(seed=7).run([emparejado], shots=256).result()[0].data.c.get_counts()
    conteos_emparejado
    return (conteos_emparejado,)


@app.cell(hide_code=True)
def _(conteos_emparejado, veredicto):
    veredicto(set(conteos_emparejado) == {"01"},
              "El qubit 2 llega al bit 0: la cadena es `'01'`. El primer argumento son los qubits y el segundo, los bits.",
              f"Ahora sale {sorted(conteos_emparejado)}. Busca que solo aparezca `'01'`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un Bell entre los qubits 1 y 3, para dos primitivas

    1. En `bell13`, de 5 qubits, entrelaza los qubits 1 y 3 (los demás quedan ociosos) y
       mídelos con `measure_active()`. Debe tener solo 2 bits clásicos.
    2. En `para_estimator` deja el **mismo circuito sin mediciones** (`remove_final_measurements`),
       que es lo que Estimator espera.

    La comprobación ejecuta `bell13` con Sampler y `para_estimator` con Estimator midiendo $Z_1Z_3$.
    """)
    return


@app.cell
def _(QuantumCircuit):
    bell13 = QuantumCircuit(5)
    # ✏️ entrelaza los qubits 1 y 3 y mídelos con measure_active()

    para_estimator = bell13   # ✏️ el mismo circuito sin mediciones
    bell13.num_clbits
    return bell13, para_estimator


@app.cell(hide_code=True)
def _(SparsePauliOp, StatevectorEstimator, StatevectorSampler, bell13, np, para_estimator, veredicto):
    _ok = bell13.num_clbits == 2 and para_estimator.num_clbits == 0
    _cuentas, _zz = {}, None
    if _ok:
        _cuentas = StatevectorSampler(seed=3).run([bell13], shots=512).result()[0].data.meas.get_counts()
        _zz = StatevectorEstimator().run(
            [(para_estimator, SparsePauliOp.from_sparse_list([("ZZ", [1, 3], 1)], num_qubits=5))]
        ).result()[0].data.evs
        _ok = set(_cuentas) == {"00", "11"} and bool(np.isclose(_zz, 1))
    veredicto(_ok,
              f"Sampler ve solo `00` y `11`, y Estimator da ⟨Z₁Z₃⟩ = {float(_zz if _ok else 0):.2f}: correlación perfecta.",
              "Necesito `bell13` con 2 bits clásicos que dé solo `00` y `11`, y `para_estimator` sin mediciones con ⟨Z₁Z₃⟩ = 1.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si enviaras `bell13` (con mediciones) a Estimator, ¿qué tendría que
    hacer Estimator con esos bits clásicos? ¿Y a Sampler un circuito sin mediciones?
    """)
    return


if __name__ == "__main__":
    app.run()
