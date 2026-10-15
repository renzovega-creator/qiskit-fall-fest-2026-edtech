import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.5 · Operadores")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit.quantum_info import Operator, Pauli, SparsePauliOp

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.5 · Operadores: práctica

    Tres misiones con `Operator` y `SparsePauliOp`: el orden de `compose`, componer sobre
    qubits concretos y un hamiltoniano que ninguna matriz densa podría guardar.
    """)
    return Operator, Pauli, SparsePauliOp, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el orden de `compose`

    `A.compose(B)` aplica primero `A` y después `B`. Antes de mirar la matriz, decide si el
    resultado es el producto $XZ$ o el producto $ZX$ y escríbelo en `orden` (`"XZ"` o `"ZX"`).
    """)
    return


@app.cell
def _(Operator, Pauli):
    A = Operator(Pauli("X"))
    B = Operator(Pauli("Z"))
    resultado = A.compose(B)

    orden = ""   # ✏️ "XZ" o "ZX"

    resultado.data
    return A, B, orden, resultado


@app.cell(hide_code=True)
def _(A, B, np, orden, resultado, veredicto):
    _matriz = {"XZ": A.data @ B.data, "ZX": B.data @ A.data}.get(orden)
    veredicto(_matriz is not None and np.allclose(resultado.data, _matriz),
              "Es $ZX$: `A.compose(B)` multiplica $B\\cdot A$, porque $A$ se aplica primero.",
              "Calcula las dos matrices a mano y compáralas con la salida de arriba.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: componer sobre qubits concretos

    `XZ` es un operador de 2 qubits: $Z$ actúa en su qubit 0 y $X$ en su qubit 1.
    Con `qargs` lo colocas dentro de un operador de 3 qubits. Ahora está en los qubits 0 y 2
    (resultado `XIZ`). Cambia `qargs` para que $X$ caiga en el qubit **1** y $Z$ en el qubit **2**,
    es decir, el resultado `ZXI`.
    """)
    return


@app.cell
def _(Operator, Pauli, np):
    grande = Operator(np.eye(8))
    colocado = grande.compose(Operator(Pauli("XZ")), qargs=[0, 2])   # ✏️ cambia qargs
    colocado.to_matrix().shape
    return (colocado,)


@app.cell(hide_code=True)
def _(Operator, Pauli, colocado, veredicto):
    veredicto(colocado == Operator(Pauli("ZXI")),
              "Resultado `ZXI`: $X$ en el qubit 1 y $Z$ en el qubit 2.",
              "Todavía no es `ZXI`. El primer elemento de `qargs` es el qubit de destino del qubit 0 de `XZ`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la cadena de Heisenberg

    Escribe `heisenberg(n)`: el `SparsePauliOp` de $n$ qubits con $\\sum_i X_iX_{i+1} + Y_iY_{i+1} + Z_iZ_{i+1}$
    sobre los vecinos de una cadena. Usa `from_sparse_list` con un bucle.

    Para 2 qubits los autovalores deben ser $-3, 1, 1, 1$, y para 50 qubits el operador
    sigue siendo manejable: una matriz densa de $2^{50}\\times 2^{50}$ no cabría en ninguna memoria.
    """)
    return


@app.cell
def _(SparsePauliOp):
    def heisenberg(n):
        terminos = []
        # ✏️ añade a `terminos` las tripletas (cadena, [i, i + 1], 1) de cada par de vecinos
        return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)
    return (heisenberg,)


@app.cell(hide_code=True)
def _(heisenberg, np, veredicto):
    _autovalores = np.sort(np.linalg.eigvalsh(heisenberg(2).to_matrix())) if len(heisenberg(2)) else []
    _ok = (np.allclose(_autovalores, [-3, 1, 1, 1]) and len(heisenberg(50)) == 3 * 49
           and np.allclose(heisenberg(3).to_matrix(), heisenberg(3).to_matrix().conj().T))
    veredicto(_ok,
              "Autovalores $-3, 1, 1, 1$ para 2 qubits, 147 términos para 50 y hermítico.",
              "Revisa: 2 qubits → autovalores $-3, 1, 1, 1$; 50 qubits → 3 · 49 términos; el operador es hermítico.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `heisenberg(50)` cabe en memoria pero `.to_matrix()` no. ¿Con qué
    operaciones sí podrías trabajar sin convertir a matriz?
    """)
    return


if __name__ == "__main__":
    app.run()
