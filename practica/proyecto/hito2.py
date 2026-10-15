import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito II")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Operator, Statevector

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito II: una cadena, muchos pasos, una magnetización

    En el hito I simulaste **2 espines** y **un paso** de tiempo. Hoy lo generalizas con lo
    que viste en la Parte II: el Hamiltoniano de una cadena de $N$ espines como `SparsePauliOp`,
    un circuito de Trotter de varios pasos y los observables de magnetización.

    $$H = J \\sum_{i} Z_i Z_{i+1} \\; + \\; h \\sum_i X_i$$

    El experimento: la cadena empieza con todos los espines en $|0\\rangle$ y se enciende de
    golpe el campo transversal. La pregunta es cómo cae la magnetización
    $M_Z = \\tfrac1N\\sum_i Z_i$ con el tiempo.
    """)
    return Operator, QuantumCircuit, SparsePauliOp, Statevector, expm, mo, np, plt, veredicto


@app.cell(hide_code=True)
def _(mo):
    N = mo.ui.slider(2, 8, step=1, value=4, label="N (espines)", show_value=True)
    J = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="J (acoplamiento ZZ)", show_value=True)
    h = mo.ui.slider(0.0, 2.0, step=0.1, value=0.5, label="h (campo transversal)", show_value=True)
    dt = mo.ui.slider(0.01, 0.5, step=0.01, value=0.1, label="dt (paso de tiempo)", show_value=True)
    pasos = mo.ui.slider(1, 40, step=1, value=20, label="pasos de Trotter", show_value=True)
    mo.vstack([mo.md("## Parámetros\nMuévelos cuando termines las misiones y mira qué cambia."), N, J, h, dt, pasos])
    return J, N, dt, h, pasos


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el Hamiltoniano de $N$ espines

    En el hito I escribiste las tres cadenas `ZZ`, `IX` y `XI`. Para $N$ espines se generan
    con `from_sparse_list`: un `ZZ` por cada par de vecinos y una `X` por cada espín.

    Antes de ejecutar, escribe en `prediccion` cuántos términos tiene `hamiltoniano(5, J, h)`.
    """)
    return


@app.cell
def _(J, N, SparsePauliOp, h):
    def hamiltoniano(n, J, h):
        terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
        return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)

    H = hamiltoniano(N.value, J.value, h.value)

    prediccion = None   # ✏️ tu apuesta: ¿cuántos términos tiene hamiltoniano(5, J, h)?

    H
    return H, hamiltoniano, prediccion


@app.cell(hide_code=True)
def _(J, SparsePauliOp, h, hamiltoniano, np, prediccion, veredicto):
    _hito1 = SparsePauliOp.from_list([("ZZ", J.value), ("IX", h.value), ("XI", h.value)])
    _coincide = bool(np.allclose(hamiltoniano(2, J.value, h.value).to_matrix(), _hito1.to_matrix()))
    veredicto(prediccion == len(hamiltoniano(5, J.value, h.value)) and _coincide,
              "Para N = 5 hay 4 + 5 = 9 términos, y con N = 2 recuperas exactamente el Hamiltoniano del hito I.",
              f"Revisa tu apuesta ({prediccion}): hay N − 1 pares de vecinos y N campos. "
              + ("" if _coincide else "Además, con N = 2 no coincide con el hito I."))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: de un paso a $N$ pasos

    `paso(n, J, h, dt)` es el paso de Trotter del hito I extendido a una cadena: `rzz` entre
    vecinos y después `rx` en cada espín. La función `trotter` solo lo aplica **una vez**.
    Modifícala para que lo repita `pasos` veces con `compose`.

    La comprobación usa $N = 3$ y 5 pasos: el circuito debe ser igual a la quinta potencia del
    paso, y con 2 espines y 1 paso debe darte el resultado del hito I.
    """)
    return


@app.cell
def _(QuantumCircuit):
    def paso(n, J, h, dt):
        qc = QuantumCircuit(n)
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
        return qc

    def trotter(n, J, h, dt, pasos):
        qc = QuantumCircuit(n)
        # ✏️ repite el paso `pasos` veces
        qc.compose(paso(n, J, h, dt), inplace=True)
        return qc
    return paso, trotter


@app.cell(hide_code=True)
def _(J, Operator, SparsePauliOp, Statevector, dt, expm, h, hamiltoniano, np, paso, trotter, veredicto):
    _n, _P = 3, 5
    _potencia = Operator(paso(_n, J.value, h.value, dt.value)).power(_P)
    _iguales = Operator(trotter(_n, J.value, h.value, dt.value, _P)).equiv(_potencia)

    _zz = expm(-1j * J.value * dt.value * SparsePauliOp("ZZ").to_matrix())
    _x = expm(-1j * h.value * dt.value * SparsePauliOp.from_list([("IX", 1), ("XI", 1)]).to_matrix())
    _hito1 = Operator(trotter(2, J.value, h.value, dt.value, 1)).equiv(Operator(_x @ _zz))

    _psi0 = np.zeros(4)
    _psi0[0] = 1
    _exacto = expm(-1j * hamiltoniano(2, J.value, h.value).to_matrix() * dt.value) @ _psi0
    _fidelidad = abs(np.vdot(_exacto, Statevector(trotter(2, J.value, h.value, dt.value, 1)).data)) ** 2
    veredicto(_iguales and _hito1,
              f"{_P} pasos = el paso elevado a la {_P}. Con 2 espines y 1 paso recuperas el hito I (fidelidad {_fidelidad:.6f}).",
              "Con N = 3 el circuito de 5 pasos todavía no es la quinta potencia del paso. "
              "¿Estás llamando a `compose` una vez por paso?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la curva de magnetización

    Dos funciones:

    1. `magnetizacion(n, eje)`: el `SparsePauliOp` $\\tfrac1n\\sum_i \\sigma_i^{\\text{eje}}$, con `eje` igual
       a `"Z"` o `"X"`.
    2. `curva_trotter(n, J, h, dt, K)`: la lista de $\\langle M_Z\\rangle$ en los tiempos $k\\,dt$ para
       $k = 0, \\dots, K$, partiendo de $|0\\dots0\\rangle$. Usa `trotter(n, J, h, dt, k)`,
       `Statevector(...)` y `expectation_value`.

    `curva_exacta` ya está escrita: aplica $e^{-iH\\,dt}$ con matrices. La comprobación compara
    ambas curvas para $N = 4$, $J = 1$, $h = 0.5$, $dt = 0.1$ y 20 pasos.
    """)
    return


@app.cell(hide_code=True)
def _(SparsePauliOp, expm, hamiltoniano, np):
    def curva_exacta(n, J, h, dt, K):
        U = expm(-1j * hamiltoniano(n, J, h).to_matrix() * dt)
        Mz = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n).to_matrix()
        psi = np.zeros(2**n, dtype=complex)
        psi[0] = 1
        valores = []
        for _ in range(K + 1):
            valores.append(float(np.real(np.vdot(psi, Mz @ psi))))
            psi = U @ psi
        return valores
    return (curva_exacta,)


@app.cell
def _(SparsePauliOp, Statevector, trotter):
    def magnetizacion(n, eje="Z"):
        terminos = []
        # ✏️ una tripleta (eje, [i], 1 / n) por cada espín
        return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)

    def curva_trotter(n, J, h, dt, K):
        valores = []
        # ✏️ para k de 0 a K: estado de trotter(n, J, h, dt, k) y valor esperado de magnetizacion(n)
        return valores
    return curva_trotter, magnetizacion


@app.cell(hide_code=True)
def _(SparsePauliOp, curva_exacta, curva_trotter, magnetizacion, np, veredicto):
    _K = 20
    _t = np.array(curva_trotter(4, 1.0, 0.5, 0.1, _K))
    _e = np.array(curva_exacta(4, 1.0, 0.5, 0.1, _K))
    _mx = magnetizacion(4, "X")
    _mx_ref = SparsePauliOp.from_sparse_list([("X", [i], 0.25) for i in range(4)], num_qubits=4)
    _ok = (len(_t) == _K + 1 and abs(_t[0] - 1) < 1e-9 and float(np.max(np.abs(_t - _e))) < 0.02
           and len(_mx) == 4 and bool(np.allclose(_mx.to_matrix(), _mx_ref.to_matrix())))
    veredicto(_ok,
              "Tu curva sigue a la exacta con un error menor que 0.02, y $M_X$ promedia las $X$ de los 4 espines.",
              "La curva debe empezar en 1, tener 21 puntos y quedar a menos de 0.02 de la exacta. "
              "Además `magnetizacion(4, \"X\")` debe tener 4 términos.")
    return


@app.cell(hide_code=True)
def _(J, N, curva_exacta, curva_trotter, dt, h, mo, pasos, plt):
    _t = curva_trotter(N.value, J.value, h.value, dt.value, pasos.value)
    if len(_t) == pasos.value + 1:
        _e = curva_exacta(N.value, J.value, h.value, dt.value, pasos.value)
        _fig, _ax = plt.subplots(figsize=(6, 3))
        _tiempos = [k * dt.value for k in range(pasos.value + 1)]
        _ax.plot(_tiempos, _e, label="exacta")
        _ax.plot(_tiempos, _t, "o", ms=4, label="Trotter")
        _ax.set_xlabel("t")
        _ax.set_ylabel("$M_Z$")
        _ax.legend()
        _salida = mo.vstack([mo.md("Mueve los controles de arriba: **dt** grande separa las dos curvas."), _fig])
    else:
        _salida = mo.md("_Completa `curva_trotter` para ver la gráfica._")
    _salida
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** con $h = 0$ el campo no actúa, y con $J = 0$ los espines no interactúan.
    ¿Cómo se ve $M_Z(t)$ en cada caso? En el hito III vas a transpilar este circuito para un
    dispositivo real: ¿qué crece con el número de pasos, el ancho o la profundidad?
    """)
    return


if __name__ == "__main__":
    app.run()
