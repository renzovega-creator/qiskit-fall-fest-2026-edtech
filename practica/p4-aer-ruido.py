import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.4 · Aer y ruido")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def ghz(n):
        qc = QuantumCircuit(n)
        qc.h(0)
        for k in range(n - 1):
            qc.cx(k, k + 1)
        qc.measure_all()
        return qc

    def conteos(qc, ruido, shots=4000):
        """Simula con Aer y el modelo de ruido dado; devuelve los conteos."""
        sim = AerSimulator(noise_model=ruido, seed_simulator=5)
        isa = generate_preset_pass_manager(1, backend=sim).run(qc)
        return sim.run(isa, shots=shots).result().get_counts()

    mo.md("""

    Tres misiones con modelos de ruido. Usan un GHZ de 6 qubits, que tiene 5 CX,
    y `AerSimulator` con semilla fija. Busca el ✅ en cada una.
    """)
    return NoiseModel, QuantumCircuit, ReadoutError, conteos, depolarizing_error, ghz, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: ideal frente a ruidoso

    El GHZ ideal solo da `000000` y `111111`. Con un error despolarizante del 2 % en
    cada CX, aparecen otras cadenas. Ejecuta y mira cuántos disparos siguen siendo
    correctos.
    """)
    return


@app.cell
def _(NoiseModel, conteos, depolarizing_error, ghz):
    n = 6
    ruido_cx = NoiseModel()
    ruido_cx.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])

    def correctos(c):
        return (c.get("0" * n, 0) + c.get("1" * n, 0)) / sum(c.values())

    ideal = correctos(conteos(ghz(n), None))
    ruidoso = correctos(conteos(ghz(n), ruido_cx))
    print(f"correctos: ideal {ideal:.3f} · con ruido {ruidoso:.3f}")
    return correctos, ideal, ruidoso


@app.cell(hide_code=True)
def _(ideal, ruidoso, veredicto):
    veredicto(ideal == 1.0 and 0.85 < ruidoso < 1.0,
              f"El ideal es perfecto y el ruido de las CX lo baja a {ruidoso:.3f}.",
              "El ideal debería dar 1.0 y el ruidoso algo menos, por encima de 0.85.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: busca la probabilidad que lo deja a la mitad

    La lección estima la supervivencia con $(1-p)^m$. Aquí $m=5$. Cambia **solo** `p` para
    que la fracción de disparos correctos caiga a un valor entre 0.55 y 0.65.
    Después compara con $(1-p)^5$: ¿la estimación es pesimista u optimista?
    """)
    return


@app.cell
def _(NoiseModel, conteos, correctos, depolarizing_error, ghz):
    p = 0.0   # ✏️ probabilidad despolarizante de cada CX

    ruido_p = NoiseModel()
    ruido_p.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    fraccion = correctos(conteos(ghz(6), ruido_p))
    print(f"p = {p} → correctos {fraccion:.3f} · estimación (1-p)^5 = {(1 - p) ** 5:.3f}")
    return (fraccion,)


@app.cell(hide_code=True)
def _(fraccion, veredicto):
    veredicto(0.55 <= fraccion <= 0.65,
              f"Fracción {fraccion:.3f}, dentro de [0.55, 0.65].",
              f"La fracción es {fraccion:.3f}. Sube `p` hasta que quede entre 0.55 y 0.65.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un error de lectura

    Un `ReadoutError` se da como una matriz de probabilidades de asignación: la fila $i$
    es lo que se registra cuando el valor verdadero es $i$. Construye un modelo con
    $P(\\text{leer }1\\,|\\,0)=0{,}05$ y $P(\\text{leer }0\\,|\\,1)=0{,}10$, y guárdalo en
    `ruido_lectura`. El circuito prepara $|1\\rangle$: se espera leer `0` en alrededor del
    10 % de los disparos.
    """)
    return


@app.cell
def _(NoiseModel, QuantumCircuit, ReadoutError, conteos):
    uno = QuantumCircuit(1)
    uno.x(0)
    uno.measure_all()

    ruido_lectura = NoiseModel()
    # ✏️ añade el ReadoutError con ruido_lectura.add_all_qubit_readout_error(...)

    c_uno = conteos(uno, ruido_lectura, shots=20000)
    lee_cero = c_uno.get("0", 0) / 20000
    print(c_uno, f"· lee 0 el {lee_cero:.1%} de las veces")
    return (lee_cero,)


@app.cell(hide_code=True)
def _(lee_cero, veredicto):
    veredicto(abs(lee_cero - 0.10) < 0.01,
              f"Lees `0` el {lee_cero:.1%} de las veces: el error de lectura funciona.",
              f"Lees `0` el {lee_cero:.1%} de las veces; deberían ser alrededor del 10 %.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el error de lectura no depende de la profundidad del circuito, pero el
    despolarizante sí. ¿Cuál de los dos te preocuparía más en un circuito de 100 CX?
    """)
    return


if __name__ == "__main__":
    app.run()
