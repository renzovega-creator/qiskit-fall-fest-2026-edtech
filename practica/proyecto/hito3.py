import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito III")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito III: transpilar para un chip real

    En los hitos anteriores construiste el paso de Trotter de la cadena de Ising

    $$H = J \\sum_{i} Z_i Z_{i+1} \\; + \\; h \\sum_i X_i$$

    y lo encadenaste para llegar a tiempos largos. Ese circuito usa `rzz` y `rx`, puertas que un
    chip de IBM no ejecuta. Hoy lo **transpilas para `FakeFez`**, un simulador con el mapa de
    acoplamiento y la base de puertas de un Heron real, y mides cuánta profundidad cuesta cada
    paso de tiempo. En el hito V esa profundidad decidirá cuántos pasos caben antes de que el ruido
    lo borre todo.
    """)
    return FakeFez, QuantumCircuit, generate_preset_pass_manager, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    J = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="J (acoplamiento ZZ)", show_value=True)
    h = mo.ui.slider(0.0, 2.0, step=0.1, value=0.5, label="h (campo transversal)", show_value=True)
    dt = mo.ui.slider(0.01, 1.0, step=0.01, value=0.1, label="dt (paso de tiempo)", show_value=True)
    mo.vstack([mo.md("## Parámetros\nMuévelos al terminar las misiones: ¿cambia la profundidad? Prueba también J = 0."), J, h, dt])
    return J, dt, h


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## El circuito de partida

    Estas dos funciones recalculan el circuito del hito II: un paso de Trotter sobre una cadena de
    `n` espines y su repetición `pasos` veces.
    """)
    return


@app.cell
def _(J, QuantumCircuit, dt, h):
    def paso(n):
        _qc = QuantumCircuit(n)
        for _k in range(n - 1):
            _qc.rzz(2 * J.value * dt.value, _k, _k + 1)
        for _k in range(n):
            _qc.rx(2 * h.value * dt.value, _k)
        return _qc

    def trotter(n, pasos):
        _qc = QuantumCircuit(n)
        for _ in range(pasos):
            _qc.compose(paso(n), inplace=True)
        return _qc

    N = 6
    return N, paso, trotter


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el circuito en `FakeFez`

    Transpila 4 pasos de Trotter de 6 espines con el nivel 3 y la semilla fija `seed_transpiler=1`.
    Antes de ejecutar, predice cuántas puertas `cz` tendrá: cada `rzz` necesita dos.
    """)
    return


@app.cell
def _(FakeFez, N, generate_preset_pass_manager, trotter):
    fez = FakeFez()
    circuito4 = trotter(N, 4)
    isa4 = generate_preset_pass_manager(3, backend=fez, seed_transpiler=1).run(circuito4)
    print("puertas:", dict(isa4.count_ops()))
    print("profundidad:", isa4.depth())
    return circuito4, fez, isa4


@app.cell(hide_code=True)
def _(N, fez, isa4, veredicto):
    _permitidas = set(fez.target.operation_names)
    _usadas = set(isa4.count_ops())
    veredicto(_usadas <= _permitidas and isa4.count_ops().get("cz") == 2 * (N - 1) * 4,
              f"Solo quedan puertas del chip, y hay {isa4.count_ops()['cz']} `cz` = 2 × {N - 1} enlaces × 4 pasos.",
              f"Salió {dict(isa4.count_ops())}. Debería ser solo puertas del chip y 2·(n−1)·pasos `cz`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: compara los niveles

    El bucle de abajo solo transpila con el nivel 0. Haz que recorra los **cuatro niveles**, del 0
    al 3, y guarde la profundidad de cada uno en `profundidad_por_nivel`.
    """)
    return


@app.cell
def _(circuito4, fez, generate_preset_pass_manager):
    profundidad_por_nivel = {}
    for nivel in range(1):   # ✏️ recorre los cuatro niveles
        _pm = generate_preset_pass_manager(nivel, backend=fez, seed_transpiler=1)
        profundidad_por_nivel[nivel] = _pm.run(circuito4).depth()
    profundidad_por_nivel
    return (profundidad_por_nivel,)


@app.cell(hide_code=True)
def _(profundidad_por_nivel, veredicto):
    _d = profundidad_por_nivel
    veredicto(sorted(_d) == [0, 1, 2, 3] and _d[0] > _d[1] > _d[2] >= _d[3],
              f"Profundidad por nivel: {_d}. Cada nivel recorta más que el anterior, y del 2 al 3 casi no queda margen.",
              f"Tienes los niveles {sorted(_d)} con profundidades {_d}. Deben estar el 0, 1, 2 y 3, y la profundidad no debe subir con el nivel.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: cuántos pasos caben

    Mide la profundidad con el nivel 3 para `1` a `10` pasos y guárdala en `profundidad_por_pasos`
    (un diccionario `pasos → profundidad`). Luego escribe `pasos_max(presupuesto)`: el mayor número
    de pasos, entre los medidos, cuya profundidad no supera el presupuesto. Devuelve `0` si
    ni siquiera cabe un paso.
    """)
    return


@app.cell
def _(N, fez, generate_preset_pass_manager, trotter):
    profundidad_por_pasos = {}
    # ✏️ rellena profundidad_por_pasos para pasos = 1..10

    def pasos_max(presupuesto):
        return 0   # ✏️ el mayor número de pasos con profundidad <= presupuesto

    pasos_max(150)
    return pasos_max, profundidad_por_pasos


@app.cell(hide_code=True)
def _(N, fez, generate_preset_pass_manager, pasos_max, profundidad_por_pasos, trotter, veredicto):
    _pm = generate_preset_pass_manager(3, backend=fez, seed_transpiler=1)
    _ref = {p: _pm.run(trotter(N, p)).depth() for p in range(1, 11)}
    _esperado = {presupuesto: max([p for p, d in _ref.items() if d <= presupuesto], default=0)
                 for presupuesto in (30, 60, 100, 150, 500)}
    _obtenido = {presupuesto: pasos_max(presupuesto) for presupuesto in _esperado}
    veredicto(profundidad_por_pasos == _ref and _obtenido == _esperado,
              f"La profundidad crece en línea recta con los pasos. Con un presupuesto de 150 caben {pasos_max(150)} pasos.",
              "Revisa que `profundidad_por_pasos` tenga los 10 pasos y que `pasos_max` devuelva el mayor `p` con `profundidad <= presupuesto`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si la profundidad crece unas 16 capas por paso, ¿cuántos pasos de Trotter te
    permite un chip cuyos qubits aguantan 150 capas? En el hito IV compararás la magnetización
    exacta con la de un simulador con ruido, y verás cuánto pesa esa profundidad.
    """)
    return


if __name__ == "__main__":
    app.run()
