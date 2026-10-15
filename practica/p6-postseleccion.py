import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.6 · Postselección")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.transpiler import PassManager
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    from qiskit_addon_utils.noise_management.post_selection import PostSelector
    from qiskit_addon_utils.noise_management.post_selection.transpiler.passes import AddPostSelectionMeasures

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    LINEA = [(0, 1), (1, 2), (2, 3)]

    ghz = QuantumCircuit(4)
    ghz.h(0)
    for _q in range(3):
        ghz.cx(_q, _q + 1)
    ghz.measure_all()
    # Tras cada medida: pulso X (20 rotaciones de π/20) y una segunda medida en meas_ps.
    ghz_ps = PassManager([AddPostSelectionMeasures(x_pulse_type="rx")]).run(ghz)

    def ejecutar(p_lectura, p_cx=0.02, shots=4000):
        """Simula el GHZ con controles y devuelve {registro: matriz booleana (disparos, bits)}."""
        modelo = NoiseModel()
        modelo.add_all_qubit_readout_error(ReadoutError([[1 - p_lectura, p_lectura], [p_lectura, 1 - p_lectura]]))
        modelo.add_all_qubit_quantum_error(depolarizing_error(p_cx, 2), ["cx"])
        memoria = AerSimulator(noise_model=modelo, seed_simulator=11).run(ghz_ps, shots=shots, memory=True).result().get_memory()
        # Aer escribe «meas_ps meas»; el bit 0 va a la derecha.
        def a_matriz(i):
            return np.array([[b == "1" for b in reversed(m.split()[i])] for m in memoria])
        return {"meas": a_matriz(1), "meas_ps": a_matriz(0)}

    def fidelidad_ghz(res, mascara=None):
        """Fracción de disparos conservados que son 0000 o 1111."""
        bits = res["meas"] if mascara is None else res["meas"][mascara]
        return float((bits.all(axis=1) | (~bits).all(axis=1)).mean())

    mo.md("""
    # 6.6 · Postselección: práctica

    Un GHZ de 4 qubits en una línea (0–1–2–3) con el control de la guía: tras medir se aplica
    un pulso X y se mide otra vez. Si el bit no se invirtió, ese disparo es sospechoso. El
    simulador es Aer con error de lectura y de CX; no necesitas cuenta.
    """)
    return (
        LINEA,
        PostSelector,
        ejecutar,
        fidelidad_ghz,
        ghz_ps,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: filtrar con `PostSelector`

    Ejecuta con un 3 % de error de lectura y calcula la máscara `node`. Antes de ejecutar,
    apuesta: ¿qué fracción de los disparos se conserva y mejora la fidelidad con el GHZ ideal?
    """)
    return


@app.cell
def _(LINEA, PostSelector, ejecutar, fidelidad_ghz, ghz_ps):
    datos = ejecutar(0.03)
    selector = PostSelector.from_circuit(ghz_ps, LINEA)
    mascara_node = selector.compute_mask(datos, strategy="node")
    print(f"conservados: {mascara_node.mean():.1%}")
    print(f"fidelidad sin filtrar: {fidelidad_ghz(datos):.3f} · con node: {fidelidad_ghz(datos, mascara_node):.3f}")
    return datos, mascara_node, selector


@app.cell(hide_code=True)
def _(datos, fidelidad_ghz, mascara_node, veredicto):
    _antes, _despues = fidelidad_ghz(datos), fidelidad_ghz(datos, mascara_node)
    veredicto(mascara_node.mean() < 1 and _despues > _antes,
              f"Se conserva el {mascara_node.mean():.1%} y la fidelidad sube de {_antes:.3f} a {_despues:.3f}. Con error de lectura independiente, filtrar ayuda.",
              "Debería descartarse una parte de los disparos y la fidelidad subir.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuánto cuesta filtrar

    Sube `p_lectura` hasta que `node` conserve **menos del 60 %** de los disparos. Cada qubit
    es una oportunidad de fallar, así que la fracción que sobrevive cae rápido.
    """)
    return


@app.cell
def _(LINEA, PostSelector, ejecutar, ghz_ps):
    p_lectura = 0.03   # ✏️ sube el error de lectura
    datos_2 = ejecutar(p_lectura)
    conservado_2 = PostSelector.from_circuit(ghz_ps, LINEA).compute_mask(datos_2, strategy="node").mean()
    conservado_2
    return conservado_2, p_lectura


@app.cell(hide_code=True)
def _(conservado_2, p_lectura, veredicto):
    veredicto(conservado_2 < 0.6,
              f"Con p_lectura = {p_lectura} solo sobrevive el {conservado_2:.1%}: reporta siempre cuántos disparos quedan.",
              f"Sobrevive el {conservado_2:.1%}. Sube `p_lectura` hasta bajar de 60 %.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la máscara a mano

    Escribe `mascara(res, estrategia)` sobre las matrices booleanas `res["meas"]` y
    `res["meas_ps"]` (una fila por disparo, una columna por qubit). Un bit «pasó» el control
    si `meas != meas_ps`.

    - `"node"`: conserva el disparo solo si **todos** los bits pasaron.
    - `"edge"`: conserva el disparo si en **cada arista** `(a, b)` de `LINEA` pasó al menos uno de los dos bits.

    La comprobación compara tu máscara con la de `PostSelector.compute_mask`.
    """)
    return


@app.cell
def _(LINEA, np):
    def mascara(res, estrategia):
        paso = res["meas"] != res["meas_ps"]
        if estrategia == "node":
            return np.ones(paso.shape[0], dtype=bool)   # ✏️ todos los bits pasaron
        return np.ones(paso.shape[0], dtype=bool)       # ✏️ cada arista de LINEA tiene al menos un bit que pasó
    return (mascara,)


@app.cell(hide_code=True)
def _(datos, mascara, np, selector, veredicto):
    _ok = all(np.array_equal(mascara(datos, e), selector.compute_mask(datos, strategy=e)) for e in ("node", "edge"))
    _n, _e = mascara(datos, "node"), mascara(datos, "edge")
    veredicto(_ok,
              f"Tus máscaras coinciden con PostSelector: node conserva {_n.mean():.1%} y edge {_e.mean():.1%}. Todo disparo de node también está en edge.",
              "Tu máscara no coincide con `PostSelector.compute_mask` en alguna estrategia.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** la guía combina `node` y `edge` con un Y lógico. Con lo que viste en la
    misión 🔴, ¿cuántos disparos conserva `node & edge` comparado con `node`? ¿Cambia algo
    la combinación?
    """)
    return


if __name__ == "__main__":
    app.run()
