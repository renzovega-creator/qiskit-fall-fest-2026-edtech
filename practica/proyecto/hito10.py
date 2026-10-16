import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito X")


@app.cell(hide_code=True)
def _():
    import io
    from datetime import date
    from importlib.metadata import version

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.linalg import expm
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito X: el informe final

    Cierras el proyecto con un informe que otra persona pueda **reproducir**: la magnetización
    de una cadena de espines tras encender de golpe el campo transversal,

    $$H = J \\sum_{i} Z_i Z_{i+1} \\; + \\; h \\sum_i X_i, \\qquad
    M(t) = \\frac{1}{N}\\sum_i \\langle Z_i \\rangle ,$$

    y la cita de Qiskit y del QPU. Este cuaderno **recalcula** los resultados de los hitos
    anteriores (el Hamiltoniano y el paso de Trotter, la curva exacta y la simulación con
    ruido) con parámetros y semillas fijos, para que el informe salga igual cada vez.
    """)
    return (AerSimulator, FakeFez, QuantumCircuit, SparsePauliOp, Statevector, date, expm, io, mo, np, plt,
            transpile, veredicto, version)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Parámetros del informe

    Una cadena abierta de $N=4$ espines que parte de $|0000\\rangle$ (todos «arriba»). Estos
    valores y las semillas van a la sección de parámetros del informe.
    """)
    return


@app.cell
def _():
    N, J, h = 4, 1.0, 1.0
    T = 2.0
    SHOTS = 4000
    SEMILLA = 7
    return J, N, SEMILLA, SHOTS, T, h


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Lo que ya construiste, recalculado

    Las funciones de abajo son los hitos II a IV en pocas líneas: el Hamiltoniano y la
    magnetización como `SparsePauliOp` (II), el paso de Trotter (I y II), la curva exacta (IV)
    y la ejecución con el modelo de ruido de `FakeFez` tras transpilar (III y IV).
    """)
    return


@app.cell
def _(
    AerSimulator, FakeFez, J, N, QuantumCircuit, SEMILLA, SHOTS, SparsePauliOp, Statevector, expm, h, np, transpile,
):
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(N - 1)] + [("X", [i], h) for i in range(N)], num_qubits=N)
    Mop = SparsePauliOp.from_sparse_list([("Z", [i], 1 / N) for i in range(N)], num_qubits=N)
    _H, _M = H.to_matrix(), Mop.to_matrix()
    _psi0 = np.zeros(2 ** N)
    _psi0[0] = 1

    def exacta(t):
        """M(t) con la evolución exacta e^{-iHt}."""
        psi = expm(-1j * _H * t) @ _psi0
        return float(np.real(np.vdot(psi, _M @ psi)))

    def paso_trotter(dt):
        qc = QuantumCircuit(N)
        for i in range(N - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(N):
            qc.rx(2 * h * dt, i)
        return qc

    def trotter(pasos, dt):
        """M tras `pasos` pasos de Trotter, sin ruido."""
        sv = Statevector.from_label("0" * N)
        paso = paso_trotter(dt)
        for _ in range(pasos):
            sv = sv.evolve(paso)
        return float(np.real(sv.expectation_value(Mop)))

    _fez = FakeFez()
    _sim = AerSimulator.from_backend(_fez)

    def circuito(pasos, dt):
        qc = QuantumCircuit(N)
        for _ in range(pasos):
            qc.compose(paso_trotter(dt), inplace=True)
        qc.measure_all()
        return transpile(qc, _fez, optimization_level=1, seed_transpiler=SEMILLA)

    def profundidad(pasos, dt):
        return circuito(pasos, dt).depth()

    def ruidosa(pasos, dt):
        """M tras `pasos` pasos de Trotter con el ruido de FakeFez."""
        cuentas = _sim.run(circuito(pasos, dt), shots=SHOTS, seed_simulator=SEMILLA).result().get_counts()
        return sum(v * sum(1 - 2 * int(b) for b in s) for s, v in cuentas.items()) / (SHOTS * N)

    return exacta, profundidad, ruidosa, trotter


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: la curva exacta y el paso de Trotter

    Ejecuta la celda: dibuja $M(t)$ exacta y la de 20 pasos de Trotter. Antes de mirar, predice:
    ¿en qué valor empieza $M$ y hacia dónde va?
    """)
    return


@app.cell
def _(T, exacta, np, plt, trotter):
    _ts = np.linspace(0, T, 81)
    _n = 20
    _dt = T / _n
    curva_exacta = [exacta(t) for t in _ts]
    trotter_20 = [trotter(k, _dt) for k in range(_n + 1)]

    _fig, _ax = plt.subplots(figsize=(6, 3))
    _ax.plot(_ts, curva_exacta, label="exacta")
    _ax.plot([k * _dt for k in range(_n + 1)], trotter_20, "o", ms=3, label="Trotter, 20 pasos")
    _ax.set_xlabel("t"); _ax.set_ylabel("M(t)"); _ax.legend()
    _fig
    return curva_exacta, trotter_20


@app.cell(hide_code=True)
def _(T, curva_exacta, exacta, trotter_20, veredicto):
    _dif = max(abs(trotter_20[k] - exacta(k * T / 20)) for k in range(21))
    veredicto(abs(curva_exacta[0] - 1) < 1e-9 and _dif < 0.01,
              f"M(0) = 1 y 20 pasos de Trotter se quedan a {_dif:.4f} de la curva exacta.",
              "M(0) debe valer 1 y 20 pasos de Trotter deben quedar a menos de 0.01 de la curva exacta.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuántos pasos usar

    Más pasos acercan Trotter a la curva exacta, pero cada paso añade profundidad al circuito
    transpilado, y la profundidad es ruido (hito III). Elige `pasos` para que el error máximo
    sobre $[0, T]$ sea **menor que 0.02** sin pasar de **200** de profundidad transpilada.
    """)
    return


@app.cell
def _(T):
    pasos = 2   # ✏️ ¿cuántos pasos de Trotter?
    dt = T / pasos
    return dt, pasos


@app.cell(hide_code=True)
def _(dt, exacta, pasos, profundidad, trotter, veredicto):
    _error = max(abs(exacta(k * dt) - trotter(k, dt)) for k in range(pasos + 1))
    _prof = profundidad(pasos, dt)
    veredicto(_error < 0.02 and _prof <= 200,
              f"{pasos} pasos: error máximo {_error:.4f} y profundidad {_prof}.",
              f"{pasos} pasos: error máximo {_error:.4f} (hace falta < 0.02) y profundidad {_prof} (máximo 200).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    La gráfica del informe junta las tres curvas con tu elección de `pasos`: exacta, Trotter sin
    ruido y Trotter con el ruido de `FakeFez`.
    """)
    return


@app.cell
def _(T, dt, exacta, np, pasos, plt, ruidosa, trotter):
    tiempos = [k * dt for k in range(pasos + 1)]
    resultados = dict(
        t=tiempos,
        exacta=[exacta(t) for t in tiempos],
        trotter=[trotter(k, dt) for k in range(pasos + 1)],
        ruidosa=[ruidosa(k, dt) for k in range(pasos + 1)],
    )
    _ts = np.linspace(0, T, 81)
    figura, _ax = plt.subplots(figsize=(6, 3))
    _ax.plot(_ts, [exacta(t) for t in _ts], label="exacta")
    _ax.plot(tiempos, resultados["trotter"], "o", ms=4, label="Trotter")
    _ax.plot(tiempos, resultados["ruidosa"], "s", ms=4, label="Trotter con ruido (FakeFez)")
    _ax.set_xlabel("t"); _ax.set_ylabel("M(t)"); _ax.legend()
    figura
    return figura, resultados


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el informe

    Escribe `informe(r, qpu, anio)`, que devuelve el texto Markdown del informe. `r` es el
    diccionario de resultados y `qpu` el QPU de tu hito V como diccionario con `name`, `version`
    y `family`, o `None` si no ejecutaste en uno real. El informe necesita:

    1. Un título que empiece con `# `.
    2. **Parámetros**: $N$, $J$, $h$, $T$, los pasos, los disparos y la semilla.
    3. **Resultados**: una tabla con una fila por instante (`t`, exacta, Trotter, con ruido).
    4. **Software**: las versiones instaladas de `qiskit`, `qiskit-aer` y `qiskit-ibm-runtime`.
    5. **Citas**: el agradecimiento, la frase del QPU
       (`In this paper we used `NOMBRE` (vVERSIÓN), an IBM Quantum FAMILIA processor.`, solo si hay QPU)
       y la referencia `IBM Quantum. https://quantum.cloud.ibm.com/, <año>`.
    """)
    return


@app.cell
def _(J, N, SEMILLA, SHOTS, T, h, version):
    AGRADECIMIENTO = ("We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
                      "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team.")
    QPU = dict(name="ibm_fez", version="1.2.8", family="Heron")

    def informe(r, qpu, anio):
        # ✏️ título, parámetros, resultados, software y citas
        return ""

    return AGRADECIMIENTO, QPU, informe


@app.cell(hide_code=True)
def _(AGRADECIMIENTO, J, N, QPU, SEMILLA, SHOTS, T, h, informe, pasos, resultados, veredicto, version):
    _texto = informe(resultados, QPU, 2026)
    _sin_qpu = informe(resultados, None, 2026)
    _frase = f"In this paper we used `{QPU['name']}` (v{QPU['version']}), an IBM Quantum {QPU['family']} processor."
    _filas = [l for l in _texto.splitlines() if l.startswith("|")]
    _ok = (_texto.startswith("# ")
           and all(version(p) in _texto for p in ("qiskit", "qiskit-aer", "qiskit-ibm-runtime"))
           and all(str(x) in _texto for x in (N, J, h, T, pasos, SHOTS, SEMILLA))
           and len(_filas) >= len(resultados["t"]) + 2
           and AGRADECIMIENTO in _texto and _frase in _texto
           and "IBM Quantum. https://quantum.cloud.ibm.com/, 2026" in _texto
           and AGRADECIMIENTO in _sin_qpu and "In this paper we used" not in _sin_qpu)
    veredicto(_ok,
              "El informe tiene parámetros, tabla de resultados, versiones y citas; sin QPU omite la frase del procesador.",
              "Faltan partes: título con `# `, parámetros, una fila de tabla por instante, las tres versiones, "
              "el agradecimiento, la frase del QPU (solo si hay QPU) y la referencia con el año.")
    return


@app.cell(hide_code=True)
def _(QPU, date, figura, informe, io, mo, resultados):
    _texto = informe(resultados, QPU, date.today().year)
    _png = io.BytesIO()
    figura.savefig(_png, format="png", dpi=150, bbox_inches="tight")
    mo.vstack([
        mo.md("## Tu informe"),
        mo.md(_texto) if _texto else mo.md("_Aún no hay informe: completa la misión 🔴._"),
        mo.hstack([mo.download(data=_texto.encode("utf-8"), filename="informe.md", label="Descargar informe.md"),
                   mo.download(data=_png.getvalue(), filename="magnetizacion.png", label="Descargar la gráfica")],
                  justify="start"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué le falta a tu informe para que otra persona obtenga los mismos
    números dentro de un año: las versiones, la semilla, el hardware, la fecha? ¿Qué parte
    cambiaría si la ejecutas en un QPU real en lugar de en el simulador?
    """)
    return


if __name__ == "__main__":
    app.run()
