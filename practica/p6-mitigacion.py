import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.3 · Mitigación: TREX, ZNE, PEA, PEC y PNA")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import DensityMatrix, SparsePauliOp
    from qiskit_aer.noise import depolarizing_error

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def plegar(qc, k):
        """Plegado global U (U† U)^k: misma operación ideal, factor de ruido 2k + 1."""
        out = qc.copy()
        for _ in range(k):
            out.compose(qc.inverse(), inplace=True)
            out.compose(qc, inplace=True)
        return out

    def esperanza(qc, lam, obs):
        """Valor esperado exacto si cada CX sufre ruido despolarizante lam (matriz densidad)."""
        rho = DensityMatrix.from_label("0" * qc.num_qubits)
        canal = depolarizing_error(lam, 2).to_quantumchannel()
        for inst in qc.data:
            qubits = [qc.find_bit(q).index for q in inst.qubits]
            rho = rho.evolve(inst.operation, qubits)
            if inst.operation.name == "cx":
                rho = rho.evolve(canal, qubits)
        return float(rho.expectation_value(obs).real)

    mo.md("""
    # 6.3 · Mitigación: práctica

    Un GHZ de 4 qubits prepara $\\langle Z_0 Z_3\\rangle = 1$. Con ruido en cada CX, ese valor
    baja. Mitigar es **estimar el 1** a partir de ejecuciones ruidosas. El simulador de esta
    práctica es exacto (sin ruido de muestreo), así que verás el sesgo limpio.
    """)
    return QuantumCircuit, SparsePauliOp, esperanza, mo, np, plegar, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: ZNE con ajuste lineal

    Medimos con los factores de ruido 1, 3 y 5 (plegando el circuito) y extrapolamos al
    factor 0 con una recta. Antes de ejecutar, apuesta: ¿la recta llega a 1, se pasa o se
    queda corta?
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, esperanza, np, plegar):
    ghz = QuantumCircuit(4)
    ghz.h(0)
    for _q in range(3):
        ghz.cx(_q, _q + 1)
    observable = SparsePauliOp("ZIIZ")
    lam = 0.02

    factores = [1, 3, 5]
    valores = [esperanza(plegar(ghz, (f - 1) // 2), lam, observable) for f in factores]
    zne_lineal = float(np.polyfit(factores, valores, 1)[1])
    print("valores a factor 1, 3, 5:", np.round(valores, 4))
    print(f"sin mitigar: {valores[0]:.4f} · ZNE lineal: {zne_lineal:.4f} · ideal: 1")
    return factores, lam, valores, zne_lineal


@app.cell(hide_code=True)
def _(valores, veredicto, zne_lineal):
    veredicto(abs(zne_lineal - 1) < abs(valores[0] - 1),
              f"ZNE lineal ({zne_lineal:.4f}) está más cerca de 1 que el valor sin mitigar ({valores[0]:.4f}), pero no llega.",
              "La extrapolación debería acercarse a 1 más que el valor medido a factor 1.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: otra curva

    Con ruido despolarizante cada puerta multiplica el valor por $(1-\\lambda)$, así que los
    puntos siguen una **exponencial** $E(c) = E_0\\,e^{-\\gamma c}$ y no una recta. Una
    exponencial es una recta en $\\ln E$. Ajusta `np.log(valores)` y vuelve con
    `np.exp(...)`. La comprobación pide un error menor que $10^{-3}$.
    """)
    return


@app.cell
def _(factores, np, valores):
    coef = np.polyfit(factores, valores, 1)   # ✏️ ajusta el logaritmo de los valores
    zne_exp = float(coef[1])                  # ✏️ deshaz el logaritmo
    zne_exp
    return (zne_exp,)


@app.cell(hide_code=True)
def _(veredicto, zne_exp):
    veredicto(abs(zne_exp - 1) < 1e-3,
              f"ZNE exponencial = {zne_exp:.4f}. Aquí es exacto porque el ruido es exactamente despolarizante; en un QPU real el modelo es una aproximación.",
              f"Obtienes {zne_exp:.4f}. Ajusta una recta a log(valores) y aplica exp al término independiente.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: PEC por mano para un qubit

    Un canal despolarizante de un qubit multiplica cada Pauli ($X$, $Y$, $Z$) por
    $1-\\lambda$ y deja $I$ igual. Para invertirlo, PEC lo escribe como una combinación de
    **insertar** $I$ (peso $a$) o una Pauli $X$, $Y$ o $Z$ (peso $b$ cada una), con
    $a + 3b = 1$ (la identidad se conserva) y $a - b = \\dfrac{1}{1-\\lambda}$ (cancela el
    factor de las Paulis). Un peso es **negativo**: por eso hay que muestrear, y el
    sobrecoste de disparos crece como $\\gamma^2$ con $\\gamma = |a| + 3|b|$.

    Escribe `pesos_pec(lam)` que devuelva `(a, b)`.
    """)
    return


@app.cell
def _():
    def pesos_pec(lam):
        a, b = 1.0, 0.0   # ✏️ resuelve las dos ecuaciones
        return a, b
    return (pesos_pec,)


@app.cell(hide_code=True)
def _(pesos_pec, veredicto):
    def _ok(lam):
        a, b = pesos_pec(lam)
        return abs(a + 3 * b - 1) < 1e-9 and abs(a - b - 1 / (1 - lam)) < 1e-9 and b < 0
    _a, _b = pesos_pec(0.05)
    veredicto(_ok(0.05) and _ok(0.1) and _ok(0.2),
              f"Con λ = 0.05: a = {_a:.4f}, b = {_b:.4f}, γ = {abs(_a) + 3 * abs(_b):.4f}. El peso b es negativo, como en PEC.",
              "Comprueba las dos ecuaciones: a + 3b = 1 y a − b = 1/(1 − λ). Además b debe salir negativo.")
    return


@app.cell(hide_code=True)
def _(mo):
    lam_slider = mo.ui.slider(0.005, 0.1, step=0.005, value=0.02, label="λ de cada puerta", show_value=True)
    n_slider = mo.ui.slider(1, 100, value=20, label="puertas del circuito", show_value=True)
    mo.vstack([mo.md("Cuántos disparos más necesita PEC si cada puerta se corrige por separado:"), lam_slider, n_slider])
    return lam_slider, n_slider


@app.cell(hide_code=True)
def _(lam_slider, mo, n_slider, pesos_pec):
    _a, _b = pesos_pec(lam_slider.value)
    _gamma = abs(_a) + 3 * abs(_b)
    mo.md(f"γ por puerta = **{_gamma:.4f}** · sobrecoste de disparos ≈ γ^(2·puertas) = **{_gamma ** (2 * n_slider.value):,.1f}×**")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ZNE necesita elegir una forma de la curva y PEC necesita conocer el
    canal. ¿Cuál de las dos suposiciones te parece más peligrosa en un QPU real? ¿Qué
    pasa con el sobrecoste de PEC si duplicas la profundidad?
    """)
    return


if __name__ == "__main__":
    app.run()
