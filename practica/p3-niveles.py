import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.3 · Niveles de optimización y parámetros")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate, efficient_su2
    from qiskit.circuit.random import random_circuit
    from qiskit.quantum_info import random_unitary
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeSherbrooke()

    mo.md("""
    # 3.3 · Niveles de optimización y parámetros: práctica

    Tres misiones con el backend falso `FakeSherbrooke`, cuya puerta de dos qubits es la ECR.
    Como las puertas de dos qubits son la mayor fuente de error, las vamos a contar.
    """)
    return (
        QuantumCircuit,
        UnitaryGate,
        backend,
        efficient_su2,
        generate_preset_pass_manager,
        mo,
        random_circuit,
        random_unitary,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: los niveles en acción

    Una unitaria aleatoria de dos qubits seguida de un SWAP. Antes de ejecutar, predice
    cuántas ECR saldrán con el nivel 3. La tabla te dice si acertaste.
    """)
    return


@app.cell
def _(QuantumCircuit, UnitaryGate, backend, generate_preset_pass_manager, random_unitary):
    unitaria_swap = QuantumCircuit(2)
    unitaria_swap.append(UnitaryGate(random_unitary(4, seed=12345)), range(2))
    unitaria_swap.swap(0, 1)

    ecr_por_nivel = {}
    for _nivel in range(4):
        _pm = generate_preset_pass_manager(_nivel, backend=backend, seed_transpiler=12345)
        ecr_por_nivel[_nivel] = _pm.run(unitaria_swap).count_ops()["ecr"]
    ecr_por_nivel
    return ecr_por_nivel, unitaria_swap


@app.cell(hide_code=True)
def _(ecr_por_nivel, veredicto):
    veredicto(ecr_por_nivel[3] < ecr_por_nivel[0],
              f"Con el nivel 3 bajas de {ecr_por_nivel[0]} a {ecr_por_nivel[3]} ECR: la unitaria y el SWAP se fusionan en un solo bloque de dos qubits.",
              "El nivel 3 debería usar menos ECR que el nivel 0. ¿Cambiaste el circuito?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: aproximar para ahorrar una ECR

    Con el nivel 3 el mismo circuito cuesta 3 ECR, el máximo que necesita cualquier unitaria de
    dos qubits. Si aceptas un error pequeño, `approximation_degree` permite sintetizarlo con menos.
    Cambia `grado` para llegar a **2 ECR** o menos sin bajar de `0.9`.
    """)
    return


@app.cell
def _(backend, generate_preset_pass_manager, unitaria_swap):
    grado = 1.0   # ✏️ 1.0 es exacto; un valor menor permite aproximar

    pm_aprox = generate_preset_pass_manager(3, backend=backend, approximation_degree=grado, seed_transpiler=12345)
    ecr_aprox = pm_aprox.run(unitaria_swap).count_ops()["ecr"]
    ecr_aprox
    return ecr_aprox, grado


@app.cell(hide_code=True)
def _(ecr_aprox, grado, veredicto):
    veredicto(ecr_aprox <= 2 and 0.9 <= grado < 1,
              f"Con `approximation_degree={grado}` bastan {ecr_aprox} ECR: una puerta ruidosa menos a cambio de un error de síntesis pequeño.",
              f"Ahora hay {ecr_aprox} ECR con grado {grado}. Busca 2 o menos, con un grado entre 0.9 y 1 (sin llegar a 1).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: elige el nivel por ti

    Escribe `mejor_nivel(qc, backend)`: transpila `qc` con los niveles 0 a 3 y devuelve el nivel
    **más bajo** que logre el menor número de puertas de dos qubits (`num_nonlocal_gates()`).
    Entre dos niveles que empatan, el más bajo gana: transpilar con menos nivel es más rápido.
    """)
    return


@app.cell
def _(generate_preset_pass_manager):
    def mejor_nivel(qc, backend, semilla=7):
        mejor, menor = 0, None
        for nivel in range(4):
            pass  # ✏️ transpila con este nivel y la semilla; si mejora el mínimo, apunta el nivel
        return mejor
    return (mejor_nivel,)


@app.cell(hide_code=True)
def _(
    backend,
    efficient_su2,
    generate_preset_pass_manager,
    mejor_nivel,
    mo,
    random_circuit,
    unitaria_swap,
    veredicto,
):
    _su2 = efficient_su2(4, entanglement="circular", reps=1).decompose()
    _su2.assign_parameters([0.3] * _su2.num_parameters, inplace=True)
    _casos = {"unitaria + SWAP": unitaria_swap, "aleatorio de 5 qubits": random_circuit(5, 5, max_operands=2, seed=11), "EfficientSU2": _su2}

    def _cuentas(qc):
        return [generate_preset_pass_manager(n, backend=backend, seed_transpiler=7).run(qc).num_nonlocal_gates() for n in range(4)]

    _filas, _bien = [], True
    for _nombre, _qc in _casos.items():
        _c = _cuentas(_qc)
        _esperado = _c.index(min(_c))
        _dado = mejor_nivel(_qc, backend)
        _bien = _bien and _dado == _esperado
        _filas.append(f"| {_nombre} | {_c} | {_esperado} | {_dado} |")
    _tabla = mo.md("| circuito | puertas 2q por nivel | esperado | tu función |\n|---|---|---|---|\n" + "\n".join(_filas))
    mo.vstack([veredicto(_bien, "Tu `mejor_nivel` elige el nivel más bajo con menos puertas de dos qubits en los tres circuitos.",
                         "Tu `mejor_nivel` no coincide en algún circuito: mira la tabla."), _tabla])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el nivel que menos puertas deja no siempre es el que da mejor resultado en hardware.
    ¿Qué más medirías antes de gastar tiempo de QPU? En el hito III compararás los niveles para el circuito del proyecto.
    """)
    return


if __name__ == "__main__":
    app.run()
