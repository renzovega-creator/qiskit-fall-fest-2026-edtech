import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.5 · Aprender el ruido")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import DensityMatrix, PauliLindbladMap, QubitSparsePauli, SparsePauliOp
    from qiskit_aer.noise import depolarizing_error

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 6.5 · Aprender el ruido: práctica

    Un modelo Pauli–Lindblad es una lista de términos $(P_j, r_j)$: una Pauli y su tasa. El
    canal es $\\Lambda=\\exp\\big(\\sum_j r_j (P_j\\cdot P_j - \\cdot)\\big)$. En la práctica
    `PauliLindbladMap` de Qiskit lo representa, y `to_pauli_lindblad_maps()` del resultado de
    NoiseLearnerV3 devuelve objetos de ese tipo.
    Aquí lo construyes, lo amplificas y, por último, **aprendes** un modelo midiendo.
    """)
    return (
        DensityMatrix,
        PauliLindbladMap,
        QuantumCircuit,
        QubitSparsePauli,
        SparsePauliOp,
        depolarizing_error,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un modelo y lo que cuesta invertirlo

    Tres términos con tasas pequeñas. La **fidelidad de Pauli** $f(Q)$ dice por cuánto se
    encoge la Pauli $Q$ tras la capa. Para PEC, invertir el modelo cuesta
    $\\gamma=e^{2\\sum_j r_j}$ por capa. Antes de ejecutar, apuesta: ¿$\\gamma$ será menor o mayor que 1?
    """)
    return


@app.cell
def _(PauliLindbladMap, QubitSparsePauli):
    modelo = PauliLindbladMap.from_list([("XI", 0.010), ("IZ", 0.005), ("ZZ", 0.002)])
    for _etiqueta in ("ZZ", "XX", "IZ"):
        print(f"fidelidad de {_etiqueta}:", round(modelo.pauli_fidelity(QubitSparsePauli.from_label(_etiqueta)), 5))
    gamma_capa = modelo.inverse().gamma()
    print("γ para invertir una capa:", round(gamma_capa, 5))
    return gamma_capa, modelo


@app.cell(hide_code=True)
def _(gamma_capa, modelo, np, veredicto):
    veredicto(abs(gamma_capa - np.exp(2 * sum(modelo.rates))) < 1e-9 and gamma_capa > 1,
              f"γ = {gamma_capa:.4f} > 1: invertir el ruido siempre cuesta disparos extra, y {gamma_capa ** 10:.3f} con 10 capas.",
              "γ debería ser exp(2·Σ rⱼ), un número algo mayor que 1.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: amplificar el ruido como hace PEA

    PEA aumenta el ruido **multiplicando las tasas** del modelo aprendido. Obtén el modelo
    amplificado por un factor 3 con `modelo.scale_rates(3)` y comprueba que el coste de
    invertirlo pasa de $\\gamma$ a $\\gamma^3$.
    """)
    return


@app.cell
def _(modelo):
    amplificado = modelo   # ✏️ el mismo modelo con las tasas multiplicadas por 3
    amplificado.rates
    return (amplificado,)


@app.cell(hide_code=True)
def _(amplificado, gamma_capa, modelo, np, veredicto):
    veredicto(np.allclose(amplificado.rates, 3 * np.asarray(modelo.rates))
              and abs(amplificado.inverse().gamma() - gamma_capa ** 3) < 1e-9,
              f"Las tasas se triplicaron y γ pasó de {gamma_capa:.4f} a {amplificado.inverse().gamma():.4f} = γ³.",
              "Las tasas del modelo amplificado deben ser 3 veces las originales.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: aprender una fidelidad midiendo

    Así se caracteriza una capa: se repite $d$ veces y se mira cómo decae un valor esperado.
    Aquí la «capa» son dos CX seguidas (la identidad si no hubiera ruido), con un 3 % de
    error despolarizante en cada CX. Mides $\\langle ZZ\\rangle$ para $d = 1, 2, 4, 8$ capas:

    $$\\langle ZZ\\rangle(d) = f^{\\,d}$$

    1. Escribe `aprender_fidelidad(ds, valores)`: ajusta una recta a $\\ln\\langle ZZ\\rangle$ y devuelve $f$.
    2. Con esa $f$, calcula la tasa del único término `XI` que reproduce la fidelidad de $ZZ$:
       $f=e^{-2r}$, es decir, $r=-\\tfrac12\\ln f$.
    """)
    return


@app.cell(hide_code=True)
def _(DensityMatrix, QuantumCircuit, SparsePauliOp, depolarizing_error):
    def zz_tras(d, lam=0.03):
        """⟨ZZ⟩ exacto tras d capas (dos CX) con ruido despolarizante lam en cada CX."""
        rho = DensityMatrix.from_label("00")
        canal = depolarizing_error(lam, 2).to_quantumchannel()
        cx = QuantumCircuit(2)
        cx.cx(0, 1)
        for _ in range(2 * d):
            rho = rho.evolve(cx).evolve(canal)
        return float(rho.expectation_value(SparsePauliOp("ZZ")).real)

    profundidades = [1, 2, 4, 8]
    medidas = [zz_tras(d) for d in profundidades]
    print("⟨ZZ⟩ para d = 1, 2, 4, 8:", [round(m, 4) for m in medidas])
    return medidas, profundidades


@app.cell
def _(PauliLindbladMap, medidas, np, profundidades):
    def aprender_fidelidad(ds, valores):
        f = 1.0   # ✏️ ajusta ln⟨ZZ⟩ = d · ln f con np.polyfit y devuelve f
        return f

    f_aprendida = aprender_fidelidad(profundidades, medidas)
    tasa = 0.0    # ✏️ r = -ln(f) / 2
    modelo_aprendido = PauliLindbladMap.from_list([("XI", tasa)])
    print(f"f = {f_aprendida:.5f} · r = {tasa:.5f}")
    return f_aprendida, modelo_aprendido, tasa


@app.cell(hide_code=True)
def _(QubitSparsePauli, f_aprendida, modelo_aprendido, veredicto):
    _verdadera = (1 - 0.03) ** 2
    _zz = modelo_aprendido.pauli_fidelity(QubitSparsePauli.from_label("ZZ"))
    veredicto(abs(f_aprendida - _verdadera) < 1e-6 and abs(_zz - _verdadera) < 1e-6,
              f"Aprendiste f = {f_aprendida:.5f}, que es (1 − 0.03)² = {_verdadera:.5f}, y tu modelo la reproduce.",
              "f debe salir (1 − 0.03)² = 0.9409 y el modelo con tu tasa debe dar esa misma fidelidad para ZZ.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** un solo término `XI` reproduce la fidelidad de $ZZ$, pero el ruido real
    de la capa tiene muchos términos. ¿Qué otras medidas necesitarías para distinguirlos?
    ¿Qué pasa con el modelo aprendido si mañana cambia la calibración?
    """)
    return


if __name__ == "__main__":
    app.run()
