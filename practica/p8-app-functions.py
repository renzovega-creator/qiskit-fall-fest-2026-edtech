import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.5 · Funciones de aplicación")


@app.cell(hide_code=True)
def _():
    import ast
    import itertools

    import marimo as mo
    import numpy as np
    from qiskit.quantum_info import SparsePauliOp

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Un problema QUBO es un diccionario como el que recibe Parity Twine en la lección:
    # "()" es la constante, "(i,)" un término lineal y "(i, j)" uno cuadrático.
    def energia(qubo, x):
        return sum(c * np.prod([x[i] for i in ast.literal_eval(clave)]) for clave, c in qubo.items())

    def minimo(qubo, n):
        """Resuelve por fuerza bruta: devuelve la x de menor energía."""
        return min(itertools.product([0, 1], repeat=n), key=lambda x: energia(qubo, x))

    mo.md("""
    # 8.5 · Funciones de aplicación: práctica

    Una función de aplicación recibe datos del dominio (un grafo, una cartera) y los convierte
    en un problema que un computador cuántico entiende: un QUBO y su Hamiltoniano de Ising.
    Tres misiones con problemas de 4 variables, resueltos por fuerza bruta en tu equipo.
    Busca el ✅ en cada una.
    """)
    return SparsePauliOp, ast, energia, itertools, minimo, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: máximo corte como QUBO

    Cada arista $(i,j)$ aporta $2x_ix_j - x_i - x_j$ al QUBO: vale $-1$ si la arista está cortada
    y $0$ si no. Minimizar la energía es maximizar el corte. Ejecuta la celda y lee la partición.
    """)
    return


@app.cell
def _(energia, minimo):
    aristas = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]

    maxcut = {"()": 0.0}
    for i, j in aristas:
        maxcut[f"({i},)"] = maxcut.get(f"({i},)", 0.0) - 1
        maxcut[f"({j},)"] = maxcut.get(f"({j},)", 0.0) - 1
        maxcut[f"({i}, {j})"] = 2.0

    x_corte = minimo(maxcut, 4)
    print("partición:", x_corte, "· aristas cortadas:", int(-energia(maxcut, x_corte)))
    return aristas, maxcut, x_corte


@app.cell(hide_code=True)
def _(aristas, maxcut, minimo, veredicto, x_corte):
    _cortadas = sum(x_corte[i] != x_corte[j] for i, j in aristas)
    veredicto(_cortadas == 4 and minimo(maxcut, 4) == x_corte,
              "Se cortan 4 de las 5 aristas: es el máximo de este grafo.",
              "Deberían cortarse 4 aristas. No cambies el QUBO.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: una restricción con penalización

    Quieres una cartera de **exactamente 2 activos** de 4. Se añade al QUBO el término
    $P\\,(\\sum_i x_i - 2)^2$, que penaliza las carteras con otro número de activos. Con un
    $P$ demasiado pequeño, el mínimo viola la restricción. Sube `penalizacion` hasta que el
    mínimo elija exactamente 2 activos.
    """)
    return


@app.cell
def _(minimo, np):
    rendimiento = np.array([0.10, 0.08, 0.06, 0.04])
    riesgo = np.array([[0.10, 0.02, 0.01, 0.00],
                       [0.02, 0.08, 0.01, 0.00],
                       [0.01, 0.01, 0.05, 0.00],
                       [0.00, 0.00, 0.00, 0.02]])

    def qubo_cartera(penalizacion, aversion=0.3, k=2):
        q = {"()": penalizacion * k * k}
        for i in range(4):
            q[f"({i},)"] = -rendimiento[i] + aversion * riesgo[i, i] + penalizacion * (1 - 2 * k)
            for j in range(i + 1, 4):
                q[f"({i}, {j})"] = 2 * aversion * riesgo[i, j] + 2 * penalizacion
        return q

    penalizacion = 0.01   # ✏️
    cartera = qubo_cartera(penalizacion)
    x_cartera = minimo(cartera, 4)
    print("cartera elegida:", x_cartera, "· activos:", sum(x_cartera))
    return cartera, penalizacion, qubo_cartera, x_cartera


@app.cell(hide_code=True)
def _(energia, itertools, qubo_cartera, veredicto, x_cartera):
    _factibles = [x for x in itertools.product([0, 1], repeat=4) if sum(x) == 2]
    _mejor = min(_factibles, key=lambda x: energia(qubo_cartera(0.0), x))
    veredicto(sum(x_cartera) == 2 and x_cartera == _mejor,
              f"El mínimo elige {x_cartera}: dos activos y la mejor cartera posible con esa restricción.",
              f"El mínimo elige {sum(x_cartera)} activos. Una penalización mayor hace caro violar la restricción.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: de QUBO a Hamiltoniano de Ising

    Para ejecutarlo, cada variable $x_i$ se sustituye por $(1 - Z_i)/2$. Escribe
    `qubo_a_ising(qubo, n)`, que devuelve `(H, constante)` con `H` un `SparsePauliOp` de $n$
    qubits, de modo que para toda $x$:

    $$E_{\\text{QUBO}}(x) = \\langle x|H|x\\rangle + \\text{constante}$$

    Un término lineal $c\\,x_i$ aporta $c/2$ a la constante y $-c/2$ a $Z_i$. Un término
    $q\\,x_ix_j$ aporta $q/4$ a la constante, $-q/4$ a $Z_i$ y a $Z_j$, y $q/4$ a $Z_iZ_j$.
    """)
    return


@app.cell
def _(SparsePauliOp, ast):
    def qubo_a_ising(qubo, n):
        constante = 0.0
        pesos = {}   # tupla de qubits → coeficiente del producto de Z sobre ellos
        for clave, c in qubo.items():
            qubits = ast.literal_eval(clave)
            # ✏️ suma a `constante` y a `pesos` según el número de variables del término
        H = SparsePauliOp.from_sparse_list(
            [("Z" * len(q), list(q), float(w)) for q, w in pesos.items()] or [("I", [0], 0.0)], num_qubits=n)
        return H, constante
    return (qubo_a_ising,)


@app.cell(hide_code=True)
def _(cartera, energia, itertools, maxcut, np, qubo_a_ising, veredicto):
    def _error(qubo):
        H, c = qubo_a_ising(qubo, 4)
        diag = np.real(np.diag(H.to_matrix()))   # el índice k tiene x_i = bit i de k (qubit 0 a la derecha)
        energias = [energia(qubo, [(k >> i) & 1 for i in range(4)]) for k in range(16)]
        return float(np.max(np.abs(diag + c - np.array(energias))))

    _e = max(_error(maxcut), _error(cartera))
    veredicto(_e < 1e-9,
              "Tu Hamiltoniano reproduce la energía de las 16 cadenas, en el máximo corte y en la cartera.",
              f"Las energías de Ising no coinciden con las del QUBO (error máximo {_e:.3g}). "
              "Revisa los signos y que sumas la constante.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el ejemplo de la guía necesita $7\\times4\\times4 = 112$ qubits. Si duplicas
    los pasos de tiempo, ¿cuántos necesitas? ¿Qué parte del problema crece más rápido?
    """)
    return


if __name__ == "__main__":
    app.run()
