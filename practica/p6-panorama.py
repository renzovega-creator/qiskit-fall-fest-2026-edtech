import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.1 · Panorama de la gestión del ruido")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    from qiskit.visualization import plot_histogram

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def modelo_ruido(p_cx, p_lectura):
        """Ruido despolarizante en cada CX y una lectura que se equivoca con probabilidad p_lectura."""
        modelo = NoiseModel()
        modelo.add_all_qubit_quantum_error(depolarizing_error(p_cx, 2), ["cx"])
        modelo.add_all_qubit_readout_error(ReadoutError([[1 - p_lectura, p_lectura], [p_lectura, 1 - p_lectura]]))
        return modelo

    def medir(qc, modelo, shots=4000):
        sim = AerSimulator(noise_model=modelo, seed_simulator=7)
        return sim.run(qc, shots=shots).result().get_counts()

    def fraccion_erronea(cuentas):
        """Fracción de disparos que ningún Bell ideal produciría: 01 o 10."""
        return (cuentas.get("01", 0) + cuentas.get("10", 0)) / sum(cuentas.values())

    mo.md("""
    # 6.1 · Panorama de la gestión del ruido: práctica

    Tres misiones para ver el ruido con tus propios números. Un estado de Bell **ideal**
    solo produce `00` y `11`; todo lo demás es ruido. Busca el ✅ en cada una.
    """)
    return QuantumCircuit, fraccion_erronea, medir, modelo_ruido, mo, plot_histogram, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el Bell que sale sucio

    El modelo de ruido tiene un 1 % de error despolarizante en cada CX y un 2 % de error de
    lectura. Antes de ejecutar, apuesta: de 4000 disparos, ¿cuántos serán `01` o `10`?
    """)
    return


@app.cell
def _(QuantumCircuit, fraccion_erronea, medir, modelo_ruido):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()

    cuentas_bell = medir(bell, modelo_ruido(0.01, 0.02))
    print(dict(sorted(cuentas_bell.items())))
    print(f"disparos erróneos: {fraccion_erronea(cuentas_bell):.1%}")
    return bell, cuentas_bell


@app.cell(hide_code=True)
def _(cuentas_bell, fraccion_erronea, veredicto):
    _f = fraccion_erronea(cuentas_bell)
    veredicto(0 < _f < 0.2,
              f"El {_f:.1%} de los disparos es erróneo: el ruido está presente pero el Bell se reconoce.",
              "Debería haber algo de `01` y `10`, pero no la mayoría. ¿Cambiaste el modelo?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: más ruido en la puerta de dos qubits

    Cambia `p_cx` para que **entre el 12 % y el 50 %** de los disparos sean erróneos. Fíjate en
    cuánto hay que subir el error de la puerta para mover el resultado: la lectura aporta una
    parte fija.
    """)
    return


@app.cell
def _(bell, fraccion_erronea, medir, modelo_ruido):
    p_cx = 0.01   # ✏️ sube este error
    cuentas_mas = medir(bell, modelo_ruido(p_cx, 0.02))
    frac_mas = fraccion_erronea(cuentas_mas)
    frac_mas
    return cuentas_mas, frac_mas, p_cx


@app.cell(hide_code=True)
def _(frac_mas, p_cx, veredicto):
    veredicto(0.12 < frac_mas < 0.5,
              f"Con `p_cx = {p_cx}` el {frac_mas:.1%} es erróneo. Ningún truco de lectura arreglaría esto: el error está en la puerta.",
              f"Ahora es el {frac_mas:.1%}. Busca un valor entre 12 % y 50 %.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: una distancia entre distribuciones

    Para comparar técnicas necesitas una cifra. Escribe `distancia_tv(a, b)`, la **distancia de
    variación total** entre dos conteos:

    $$\\mathrm{TV}(a,b) = \\tfrac12 \\sum_x \\big|\\,p_a(x) - p_b(x)\\,\\big|$$

    donde $p(x)$ es la fracción de disparos de la cadena $x$ (suma sobre todas las cadenas que
    aparezcan en alguno). Vale 0 si son iguales y 1 si no comparten ninguna cadena.
    """)
    return


@app.cell
def _():
    def distancia_tv(a, b):
        total = 0.0
        # ✏️ normaliza cada conteo y suma |pa - pb| sobre todas las cadenas
        return total
    return (distancia_tv,)


@app.cell(hide_code=True)
def _(distancia_tv, veredicto):
    _bien = (
        abs(distancia_tv({"00": 5, "11": 5}, {"00": 50, "11": 50})) < 1e-9
        and abs(distancia_tv({"00": 10}, {"11": 10}) - 1) < 1e-9
        and abs(distancia_tv({"00": 3, "11": 1}, {"00": 1, "11": 1}) - 0.25) < 1e-9
    )
    veredicto(_bien,
              "Tu `distancia_tv` da 0 para distribuciones iguales, 1 para disjuntas y 0.25 en el caso 3:1 contra 1:1.",
              "Prueba con `{'00': 10}` contra `{'11': 10}` (debe dar 1) y con conteos de distinto tamaño que tengan la misma proporción (debe dar 0).")
    return


@app.cell(hide_code=True)
def _(mo):
    p_slider = mo.ui.slider(0.0, 0.3, step=0.01, value=0.01, label="error de la CX", show_value=True)
    p_slider
    return (p_slider,)


@app.cell(hide_code=True)
def _(bell, distancia_tv, medir, modelo_ruido, mo, p_slider, plot_histogram):
    _c = medir(bell, modelo_ruido(p_slider.value, 0.02))
    _ideal = {"00": 0.5, "11": 0.5}
    mo.vstack([
        mo.md(f"Distancia al Bell ideal: **{distancia_tv(_c, _ideal):.3f}**"),
        plot_histogram(_c),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si la distancia al ideal es 0.45, ¿tiene sentido gastar disparos en
    mitigar? ¿Qué cambiarías primero, el circuito o la técnica?
    """)
    return


if __name__ == "__main__":
    app.run()
