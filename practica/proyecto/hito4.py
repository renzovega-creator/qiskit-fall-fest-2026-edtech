import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito IV")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito IV: la magnetización en el tiempo

    Hasta ahora tienes el modelo y su circuito. Este hito responde la pregunta del
    proyecto con simuladores: **¿cómo evoluciona la magnetización** de una cadena de 4
    espines tras encender de golpe el campo transversal, y **cuánto se desvía** cuando
    el computador tiene ruido?

    $$H = J \\sum_{i} Z_i Z_{i+1} \\; + \\; h \\sum_i X_i \\qquad
    M(t) = \\frac{1}{N}\\sum_i \\langle Z_i\\rangle$$

    Empezamos en $|0000\\rangle$ (todos los espines alineados, $M=1$). El resultado
    exacto es la referencia; el de Aer con ruido anticipa lo que verás en el QPU del hito V.
    """)
    return (
        AerEstimator,
        NoiseModel,
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        depolarizing_error,
        expm,
        generate_preset_pass_manager,
        mo,
        np,
        plt,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    J = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="J (acoplamiento ZZ)", show_value=True)
    h = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="h (campo transversal)", show_value=True)
    dt = mo.ui.slider(0.02, 0.3, step=0.01, value=0.1, label="dt (paso de tiempo)", show_value=True)
    p = mo.ui.slider(0.0, 0.05, step=0.005, value=0.01, label="p (error despolarizante por CX)", show_value=True)
    mo.vstack([mo.md("## Parámetros\nMuévelos cuando termines las misiones y mira qué cambia."), J, h, dt, p])
    return J, dt, h, p


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Lo que ya construiste (hitos I a III)

    Aquí se recalcula todo desde cero, para que este cuaderno se baste solo: el
    Hamiltoniano y el observable como `SparsePauliOp`, el circuito de $k$ pasos de
    Trotter (el paso del hito I repetido, hito II) y la transpilación para el simulador
    (hito III). Léelo y sigue.
    """)
    return


@app.cell
def _(J, QuantumCircuit, SparsePauliOp, dt, generate_preset_pass_manager, h, np):
    N = 4
    PASOS = 20

    def pauli(ops):
        """Cadena de Pauli con la letra dada en cada qubit; Qiskit pone el qubit 0 a la derecha."""
        s = ["I"] * N
        for q, letra in ops:
            s[N - 1 - q] = letra
        return "".join(s)

    H = SparsePauliOp.from_list(
        [(pauli([(i, "Z"), (i + 1, "Z")]), J.value) for i in range(N - 1)]
        + [(pauli([(i, "X")]), h.value) for i in range(N)]
    )
    M = SparsePauliOp.from_list([(pauli([(i, "Z")]), 1 / N) for i in range(N)])

    def trotter(k):
        """k pasos de Trotter: primero los ZZ de cada enlace, después las X de cada espín."""
        qc = QuantumCircuit(N)
        for _ in range(k):
            for i in range(N - 1):
                qc.rzz(2 * J.value * dt.value, i, i + 1)
            for i in range(N):
                qc.rx(2 * h.value * dt.value, i)
        return qc

    tiempos = dt.value * np.arange(PASOS + 1)
    pm = generate_preset_pass_manager(1, basis_gates=["cx", "rz", "sx", "x"])
    return H, M, N, PASOS, pm, tiempos, trotter


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: la curva exacta y la de Trotter

    La referencia exacta sale de $e^{-iHt}|0000\\rangle$. La del circuito, de
    `Statevector.from_instruction` sobre cada circuito de $k$ pasos, sin ruido. Ejecuta y
    mira cuánto se separan.
    """)
    return


@app.cell
def _(H, M, N, PASOS, Statevector, expm, np, tiempos, trotter):
    _psi0 = np.zeros(2**N)
    _psi0[0] = 1
    _Hm, _Mm = H.to_matrix(), M.to_matrix()
    exacta = np.array([np.vdot(psi, _Mm @ psi).real for psi in (expm(-1j * _Hm * t) @ _psi0 for t in tiempos)])
    ideal = np.array([Statevector.from_instruction(trotter(k)).expectation_value(M).real for k in range(PASOS + 1)])
    error_trotter = float(np.abs(ideal - exacta).max())
    print(f"M(t) exacta, primeros valores: {exacta[:5].round(3)}")
    print(f"error máximo de Trotter sin ruido: {error_trotter:.4f}")
    return error_trotter, exacta, ideal


@app.cell(hide_code=True)
def _(dt, error_trotter, veredicto):
    veredicto(error_trotter < 0.05,
              f"Con dt = {dt.value} el circuito sigue a la curva exacta (error máximo {error_trotter:.4f}).",
              f"Con dt = {dt.value} el error de Trotter llega a {error_trotter:.3f}: baja el paso de tiempo.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: añade el ruido

    `AerEstimator` calcula $M$ para cada circuito transpilado. Falta el modelo de ruido:
    añade un error despolarizante de probabilidad `p.value` a cada `cx` (en el hito V,
    el QPU hará esto de verdad). Fíjate en que la curva ruidosa se aplana hacia 0.
    """)
    return


@app.cell
def _(AerEstimator, M, NoiseModel, PASOS, depolarizing_error, np, p, pm, trotter):
    ruido = NoiseModel()
    # ✏️ añade el error despolarizante de dos qubits, probabilidad p.value, a la puerta "cx"

    estimator = AerEstimator(options=dict(backend_options=dict(noise_model=ruido), run_options=dict(seed=1)))
    _pubs = [(pm.run(trotter(k)), M) for k in range(PASOS + 1)]
    ruidosa = np.array([float(r.data.evs) for r in estimator.run(_pubs).result()])
    print(f"M(t) con ruido, primeros valores: {ruidosa[:5].round(3)}")
    return (ruidosa,)


@app.cell(hide_code=True)
def _(ideal, np, p, ruidosa, veredicto):
    _desvio = float(np.abs(ruidosa - ideal).max())
    veredicto(_desvio > 0.02,
              f"El ruido ya se nota: la curva se separa hasta {_desvio:.3f} de la ideal (p = {p.value}).",
              f"La curva ruidosa casi no se separa ({_desvio:.4f}). ¿Añadiste el error a `ruido`? ¿Es p > 0?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: ¿hasta cuándo te puedes fiar?

    La pregunta que decide cuántos pasos pedirle al QPU: ¿en qué instante la simulación con
    ruido se aleja de la exacta más que una tolerancia? Escribe
    `tiempo_de_validez(tiempos, referencia, medida, tol)`, que devuelva el **primer**
    tiempo en que $|\\text{medida}-\\text{referencia}|>$ `tol`, o `None` si nunca ocurre.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    tol = mo.ui.slider(0.01, 0.2, step=0.01, value=0.05, label="tolerancia", show_value=True)
    tol
    return (tol,)


@app.cell
def _(exacta, ruidosa, tiempos, tol):
    def tiempo_de_validez(tiempos, referencia, medida, tol):
        # ✏️ recorre los instantes y devuelve el primero que supera la tolerancia
        return None

    t_valido = tiempo_de_validez(tiempos, exacta, ruidosa, tol.value)
    return t_valido, tiempo_de_validez


@app.cell(hide_code=True)
def _(tiempo_de_validez, tol, t_valido, veredicto):
    _prueba = tiempo_de_validez([0, 1, 2, 3], [1, 1, 1, 1], [1, 0.95, 0.8, 0.5], 0.1)
    _nunca = tiempo_de_validez([0, 1], [1, 1], [1, 1.05], 0.1)
    veredicto(_prueba == 2 and _nunca is None,
              "Tu función pasa los casos de prueba. "
              + (f"Con tolerancia {tol.value}, la simulación ruidosa deja de fiarse en t = {float(t_valido):.2f}."
                 if t_valido is not None else f"Con tolerancia {tol.value} nunca se separa en este intervalo."),
              "En [0, 1, 2, 3] con error [0, .05, .2, .5] y tol = 0.1 debe devolver 2; si nunca supera la tolerancia, `None`.")
    return


@app.cell(hide_code=True)
def _(exacta, ideal, plt, ruidosa, t_valido, tiempos):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(tiempos, exacta, "k-", label="exacta")
    ax.plot(tiempos, ideal, "o", ms=4, label="Trotter sin ruido")
    ax.plot(tiempos, ruidosa, "s--", ms=4, label="Aer con ruido")
    if t_valido is not None:
        ax.axvline(t_valido, color="tab:red", lw=1, ls=":", label="fin de la validez")
    ax.set_xlabel("t")
    ax.set_ylabel("M(t)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si el QPU del hito V tiene un error por CX parecido a `p`, ¿cuántos
    pasos de Trotter puedes pedirle antes de que el ruido tape la física? Anota tu
    estimación: la comprobarás con la ejecución real.
    """)
    return


if __name__ == "__main__":
    app.run()
