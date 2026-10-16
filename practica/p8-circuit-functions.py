import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.4 · Funciones de circuito")


@app.cell(hide_code=True)
def _():
    import math

    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 8.4 · Funciones de circuito: práctica

    Una función de circuito como QESEM cobra tiempo de QPU que crece con el inverso del
    cuadrado de la precisión que pides. Tres misiones para comprobarlo con el estimador
    exacto de tu equipo, que muestrea igual que un QPU ideal. Busca el ✅ en cada una.
    """)
    return QuantumCircuit, SparsePauliOp, StatevectorEstimator, math, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: precisión, disparos y dispersión

    `StatevectorEstimator(default_precision=ε)` toma $\\lceil 1/ε^2 \\rceil$ disparos por término.
    Para cada ε, la celda repite la estimación 60 veces y mide cuánto varían los resultados.
    Mira cuántos disparos cuesta cada precisión y qué dispersión obtienes.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, StatevectorEstimator, math, np):
    circuito = QuantumCircuit(2)
    circuito.ry(0.9, 0)
    circuito.cx(0, 1)
    observable = SparsePauliOp("ZZ")

    def dispersion(eps, repeticiones=60):
        valores = [StatevectorEstimator(default_precision=eps, seed=s).run([(circuito, observable)]).result()[0].data.evs
                   for s in range(repeticiones)]
        return float(np.std(valores))

    tabla = {eps: (math.ceil(1 / eps**2), dispersion(eps)) for eps in (0.1, 0.05, 0.025)}
    for eps, (disparos, desv) in tabla.items():
        print(f"ε = {eps:<6} disparos = {disparos:<5} dispersión = {desv:.3f}")
    return (tabla,)


@app.cell(hide_code=True)
def _(tabla, veredicto):
    _d = [tabla[e][0] for e in (0.1, 0.05, 0.025)]
    _s = [tabla[e][1] for e in (0.1, 0.05, 0.025)]
    veredicto(_d[1] == 4 * _d[0] and _d[2] == 4 * _d[1] and 1.7 < _s[0] / _s[1] < 2.3,
              "Mitad de error: cuatro veces más disparos. La dispersión sigue a ε.",
              "No cambies la fórmula de los disparos: debería ser $\\lceil 1/ε^2\\rceil$.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: el estimador de tiempo

    QESEM modela su tiempo de QPU como

    $$T_{QPU} \\approx a\\,\\frac{e^{\\alpha V_a}}{\\epsilon^2} + b$$

    donde $V_a$ es el volumen activo del circuito, $a$ y $b$ son constantes del
    dispositivo (la $\\alpha$ de la lección ya incluye el factor $IF$). La función de abajo tiene
    mal el exponente de la precisión. Corrígela.
    """)
    return


@app.cell
def _(math):
    def tiempo_qpu(eps, va, a=0.004, alfa=0.35, b=60.0):
        """Segundos de QPU para precisión `eps` y volumen activo `va`."""
        return a * math.exp(alfa * va) / eps + b   # ✏️ el exponente de eps
    return (tiempo_qpu,)


@app.cell(hide_code=True)
def _(math, tiempo_qpu, veredicto):
    _b = 60.0
    _x = (tiempo_qpu(0.01, 20) - _b)
    _cuatro = abs((tiempo_qpu(0.005, 20) - _b) / _x - 4) < 1e-9
    _vol = abs((tiempo_qpu(0.01, 21) - _b) / _x - math.exp(0.35)) < 1e-9
    veredicto(_cuatro and _vol,
              f"Mitad de ε = cuatro veces más tiempo; y cada unidad de volumen lo multiplica por $e^α$ = {math.exp(0.35):.2f}.",
              "Al reducir ε a la mitad, la parte variable del tiempo debe crecer ×4.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: ¿qué precisión me alcanza?

    Escribe `precision_alcanzable(t_max, va)`: la precisión $ε$ más fina que cabe en un
    presupuesto de `t_max` segundos de QPU para un circuito de volumen `va`. Es la inversa de
    `tiempo_qpu`. Si `t_max` no supera el tiempo fijo $b$, lanza `ValueError`.
    """)
    return


@app.cell
def _(math):
    def precision_alcanzable(t_max, va, a=0.004, alfa=0.35, b=60.0):
        # ✏️ despeja ε de tiempo_qpu; ValueError si t_max <= b
        return None
    return (precision_alcanzable,)


@app.cell(hide_code=True)
def _(precision_alcanzable, tiempo_qpu, veredicto):
    def _roundtrip():
        for eps, va in [(0.02, 10), (0.01, 20), (0.005, 25)]:
            if precision_alcanzable(tiempo_qpu(eps, va), va) is None:
                return False
            if abs(precision_alcanzable(tiempo_qpu(eps, va), va) - eps) > 1e-9:
                return False
        return True

    def _error():
        try:
            precision_alcanzable(30.0, 10)
        except ValueError:
            return True
        return False

    veredicto(_roundtrip() and _error(),
              "Tu función invierte el tiempo: el presupuesto fija la precisión que te puedes permitir.",
              "Para $ε$ y $V_a$ dados, `precision_alcanzable(tiempo_qpu(ε, va), va)` debe devolver $ε$; "
              "y con `t_max <= b` debe lanzar `ValueError`. (Primero arregla `tiempo_qpu`.)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** con un presupuesto fijo, ¿cuánta precisión pierdes al añadir 5 unidades
    de volumen activo? ¿Por qué QESEM ofrece `estimate_time_only` antes de gastar el QPU?
    """)
    return


if __name__ == "__main__":
    app.run()
