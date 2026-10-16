import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.1 · Circuitos dinámicos en hardware")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from qiskit.result import marginal_counts
    from qiskit_aer import AerSimulator

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def correr(qc, shots=1000):
        return AerSimulator(seed_simulator=7).run(qc, shots=shots).result().get_counts()

    mo.md("""
    # 7.1 · Circuitos dinámicos en hardware: práctica

    Tres misiones con circuitos que deciden a mitad de camino. Se ejecutan en el simulador
    Aer de tu equipo, sin cuenta ni red. Busca el ✅ en cada una.
    """)
    return ClassicalRegister, QuantumCircuit, QuantumRegister, correr, marginal_counts, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: corregir una medición

    Prepara $|+\\rangle$ con una Hadamard y mídelo. Si salió `1`, una `X` devuelve el qubit a
    `|0⟩`; después se mide otra vez. **Antes de ejecutar, predice** qué verás en la segunda
    medición.
    """)
    return


@app.cell
def _(QuantumCircuit, correr, marginal_counts):
    correccion = QuantumCircuit(1, 2)
    correccion.h(0)
    correccion.measure(0, 0)
    with correccion.if_test((correccion.clbits[0], 1)):
        correccion.x(0)
    correccion.measure(0, 1)

    segunda = marginal_counts(correr(correccion), [1])
    segunda
    return correccion, segunda


@app.cell(hide_code=True)
def _(correccion, mo, segunda, veredicto):
    mo.vstack([
        correccion.draw("mpl"),
        veredicto(set(segunda) == {"0"},
                  "La segunda medición da siempre `0`: el `if` corrigió el qubit cuando hizo falta.",
                  "La segunda medición debería dar siempre `0`. ¿Cambiaste el circuito?"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un solo `if` en lugar de dos anidados

    El hardware de IBM no admite `if` anidados. Este circuito mide los qubits 0 y 1 y aplica
    una `X` al qubit 2 solo si **ambos** valen 1. Reemplaza los dos `if` por **uno** que
    compare el registro `cr` con `0b11`.
    """)
    return


@app.cell
def _(ClassicalRegister, QuantumCircuit, QuantumRegister):
    cr = ClassicalRegister(2, "cr")
    res = ClassicalRegister(1, "res")
    qc = QuantumCircuit(QuantumRegister(3), cr, res)
    qc.h([0, 1])
    qc.measure([0, 1], cr)
    # ✏️ un solo `if` sobre el registro `cr`
    with qc.if_test((cr[0], 1)):
        with qc.if_test((cr[1], 1)):
            qc.x(2)
    qc.measure(2, res)
    qc.draw("mpl")
    return (qc,)


@app.cell(hide_code=True)
def _(correr, qc, veredicto):
    def _ramas(c):
        n = 0
        for inst in c.data:
            if inst.operation.name == "if_else":
                n += 1 + sum(_ramas(b) for b in inst.operation.blocks)
        return n

    _cuenta = correr(qc, 2000)
    _logica = all((k.split()[0] == "1") == (k.split()[1] == "11") for k in _cuenta)
    _n = _ramas(qc)
    veredicto(_n == 1 and _logica,
              "Un solo `if` sobre `cr`: la `X` se aplica solo cuando `cr` vale `11`.",
              f"Hay {_n} instrucciones `if` (debe haber 1) y la lógica "
              f"{'se conserva' if _logica else 'cambió: `res` debe valer 1 solo si `cr` es 11'}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: ¿lo admite el hardware?

    Escribe `es_valido(qc)`, que devuelva `True` si un circuito respeta los límites de la
    lección y `False` si no:

    - ni `for_loop`, ni `while_loop`, ni `switch_case`;
    - ningún `if` dentro de otro `if`;
    - ni `measure` ni `reset` dentro de un `if`;
    - el operando de un `if` tiene como máximo 32 bits (un registro de 50 bits entero no
      vale; un solo bit de él, sí).

    Pista: cada instrucción es `inst.operation`; las ramas de un `if` están en
    `op.blocks`, y su condición en `op.condition`.
    """)
    return


@app.cell
def _():
    def es_valido(qc, dentro=False):
        """True si el circuito cumple los límites del hardware de IBM."""
        return True   # ✏️ tu código aquí
    return (es_valido,)


@app.cell(hide_code=True)
def _(ClassicalRegister, QuantumCircuit, es_valido, veredicto):
    def _caso(construir):
        qc = QuantumCircuit(3, 3)
        cr = ClassicalRegister(50, "grande")
        qc.add_register(cr)
        construir(qc, cr)
        return qc

    def _if_simple(qc, cr):
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(1)

    def _if_else(qc, cr):
        with qc.if_test((qc.clbits[0], 1)) as _otro:
            qc.x(1)
        with _otro:
            qc.z(1)

    def _un_bit_de_50(qc, cr):
        with qc.if_test((cr[5], 1)):
            qc.x(1)

    def _registro_50(qc, cr):
        with qc.if_test((cr, 15)):
            qc.x(1)

    def _anidado(qc, cr):
        with qc.if_test((qc.clbits[0], 1)):
            with qc.if_test((qc.clbits[1], 1)):
                qc.x(2)

    def _medir_dentro(qc, cr):
        with qc.if_test((qc.clbits[0], 1)):
            qc.measure(1, 2)

    def _reset_dentro(qc, cr):
        with qc.if_test((qc.clbits[0], 1)):
            qc.reset(1)

    def _for(qc, cr):
        with qc.for_loop(range(3)):
            qc.x(1)

    def _while(qc, cr):
        with qc.while_loop((qc.clbits[0], 0)):
            qc.h(0)
            qc.measure(0, 0)

    def _switch(qc, cr):
        with qc.switch(qc.clbits[0]) as _caso_:
            with _caso_(0):
                qc.x(1)

    _casos = [(_if_simple, True), (_if_else, True), (_un_bit_de_50, True), (_registro_50, False),
              (_anidado, False), (_medir_dentro, False), (_reset_dentro, False), (_for, False),
              (_while, False), (_switch, False)]
    _fallos = [c.__name__.strip("_") for c, esperado in _casos if es_valido(_caso(c)) != esperado]
    veredicto(not _fallos,
              f"`es_valido` acierta en los {len(_casos)} circuitos de prueba.",
              f"`es_valido` se equivoca en: {', '.join(_fallos)}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** medir a mitad de circuito suele tardar más que una puerta de dos qubits.
    ¿Cuándo compensa un circuito dinámico frente a uno estático más profundo?
    """)
    return


if __name__ == "__main__":
    app.run()
