import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.2 · Las seis etapas del transpilador")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit.random import random_circuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 3.2 · Las seis etapas: práctica

    Tres misiones sobre lo que hacen el layout y el routing: cuántas CNOT cuesta mover estados,
    cómo un buen layout evita SWAP y por qué conviene transpilar varias veces.
    """)
    return CouplingMap, GenericBackendV2, QuantumCircuit, generate_preset_pass_manager, mo, random_circuit, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un GHZ en línea

    Un GHZ de 15 qubits con todas las CNOT desde el qubit 0, sobre un chip donde los qubits
    están en línea. El circuito original tiene **14** CNOT. Antes de ejecutar, predice cuántas
    tendrá con el nivel 0: todo lo que sobre son CNOT de los SWAP del routing.
    """)
    return


@app.cell
def _(CouplingMap, GenericBackendV2, QuantumCircuit, generate_preset_pass_manager):
    chip = GenericBackendV2(15, coupling_map=CouplingMap.from_line(15), seed=1)
    ghz = QuantumCircuit(15)
    ghz.h(0)
    ghz.cx(0, range(1, 15))

    cx_por_nivel = {}
    for _nivel in range(4):
        _pm = generate_preset_pass_manager(_nivel, backend=chip, seed_transpiler=1234)
        cx_por_nivel[_nivel] = _pm.run(ghz).count_ops()["cx"]
    cx_por_nivel
    return (cx_por_nivel,)


@app.cell(hide_code=True)
def _(cx_por_nivel, veredicto):
    veredicto(cx_por_nivel[0] > cx_por_nivel[3] > 14,
              f"Del nivel 0 al 3 bajas de {cx_por_nivel[0]} a {cx_por_nivel[3]} CNOT; las 14 originales son el mínimo posible.",
              "El nivel 3 debería usar menos CNOT que el nivel 0, y más que las 14 originales.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un layout sin SWAP

    El chip es un árbol en forma de T: el qubit físico 1 tiene tres vecinos (0, 2 y 3) y el 0 solo uno.
    El circuito tiene un qubit central, el virtual 0, que hace CNOT con los otros tres.
    Con el nivel 0 el transpilador usa **tal cual** el `initial_layout` que le des
    (con nivel 1 o más, `VF2Layout` buscaría uno perfecto por su cuenta).

    Cambia `layout_inicial` para que no haga falta ningún SWAP.
    """)
    return


@app.cell
def _(CouplingMap, QuantumCircuit, generate_preset_pass_manager):
    chip_t = CouplingMap([[0, 1], [1, 2], [1, 3], [3, 4]])
    chip_t.make_symmetric()

    estrella = QuantumCircuit(4)
    estrella.cx(0, 1)
    estrella.cx(0, 2)
    estrella.cx(0, 3)

    # el elemento i es el qubit físico donde va el virtual i
    layout_inicial = [0, 1, 2, 3]   # ✏️ ¿en qué qubit físico va el virtual 0?

    pm_estrella = generate_preset_pass_manager(0, coupling_map=chip_t, initial_layout=layout_inicial, seed_transpiler=1)
    swaps_estrella = pm_estrella.run(estrella).count_ops().get("swap", 0)
    swaps_estrella
    return layout_inicial, swaps_estrella


@app.cell(hide_code=True)
def _(layout_inicial, swaps_estrella, veredicto):
    veredicto(swaps_estrella == 0,
              f"Con el layout {layout_inicial} no hace falta ningún SWAP: el qubit central cayó en el físico de tres vecinos.",
              f"Con el layout {layout_inicial} el routing inserta {swaps_estrella} SWAP. ¿Qué qubit físico tiene tres vecinos?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: transpila varias veces y quédate con el mejor

    El routing de Sabre es estocástico: otra `seed_transpiler` puede dar otro circuito.
    Escribe `mejor_de(qc, semillas)`: transpila `qc` con cada semilla (nivel 1, sobre una
    cuadrícula de 3×3) y devuelve **el circuito con menos CNOT**.
    """)
    return


@app.cell
def _(CouplingMap, generate_preset_pass_manager, random_circuit):
    cuadricula = CouplingMap.from_grid(3, 3)
    puertas_base = ["cx", "rz", "sx", "x"]
    aleatorio = random_circuit(9, 6, max_operands=2, seed=3)

    def transpilar(qc, semilla):
        pm = generate_preset_pass_manager(1, coupling_map=cuadricula, basis_gates=puertas_base, seed_transpiler=semilla)
        return pm.run(qc)

    def mejor_de(qc, semillas):
        mejor = None
        for semilla in semillas:
            pass  # ✏️ transpila con esta semilla (puedes usar `transpilar`) y quédate con el de menos CNOT
        return mejor
    return aleatorio, mejor_de, transpilar


@app.cell(hide_code=True)
def _(aleatorio, mejor_de, mo, transpilar, veredicto):
    _cx = [transpilar(aleatorio, s).count_ops().get("cx", 0) for s in range(10)]
    _elegido = mejor_de(aleatorio, range(10))
    _n = None if _elegido is None else _elegido.count_ops().get("cx", 0)
    _v = veredicto(_n == min(_cx),
                   f"Tu función devuelve el circuito de {_n} CNOT: el mejor de 10 semillas. Con una sola semilla (la 0) habrías tenido {_cx[0]}.",
                   f"Las CNOT por semilla son {_cx}. Tu función devuelve {_n}; debería devolver el circuito de {min(_cx)}.")
    mo.vstack([_v, mo.md("CNOT por semilla: " + ", ".join(map(str, _cx)))])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿cuántas semillas pagarían la pena antes de que el tiempo de transpilación
    pese más que el ahorro de CNOT? En el hito III verás cómo crece la profundidad con cada paso de Trotter.
    """)
    return


if __name__ == "__main__":
    app.run()
