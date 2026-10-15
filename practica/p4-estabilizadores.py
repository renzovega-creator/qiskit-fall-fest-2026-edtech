import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.5 · Circuitos de Clifford")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import efficient_su2
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer import AerSimulator

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    simulador = AerSimulator(method="stabilizer", seed_simulator=3)
    pm = generate_preset_pass_manager(1, simulador)

    def conteos_stabilizer(qc, shots=1024):
        return simulador.run(pm.run(qc), shots=shots).result().get_counts()

    mo.md("""

    Tres misiones con el método `stabilizer` de Aer. Busca el ✅ en cada una.
    """)
    return QuantumCircuit, conteos_stabilizer, efficient_su2, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un GHZ de 100 qubits

    Un vector de estado de 100 qubits no cabe en ninguna memoria. El método `stabilizer`
    lo simula al instante porque el GHZ es de Clifford. Ejecuta y mira las cadenas.
    """)
    return


@app.cell
def _(QuantumCircuit, conteos_stabilizer):
    ghz100 = QuantumCircuit(100)
    ghz100.h(0)
    for k in range(99):
        ghz100.cx(k, k + 1)
    ghz100.measure_all()

    conteos_ghz = conteos_stabilizer(ghz100)
    print(len(conteos_ghz), "cadenas distintas de", len(next(iter(conteos_ghz))), "bits")
    return (conteos_ghz,)


@app.cell(hide_code=True)
def _(conteos_ghz, veredicto):
    veredicto(set(conteos_ghz) == {"0" * 100, "1" * 100},
              "Solo `0…0` y `1…1`, con 100 qubits y sin esfuerzo.",
              "Deberían aparecer solo dos cadenas: todo ceros o todo unos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: haz que el circuito sea de Clifford

    Este circuito lleva una rotación $R_z(\\pi/4)$, que no es de Clifford, y el simulador
    de estabilizadores la rechaza. Cambia **solo el ángulo** para que corra. La rotación
    debe seguir en el circuito.
    """)
    return


@app.cell
def _(QuantumCircuit, conteos_stabilizer, np):
    angulo = np.pi / 4   # ✏️ un múltiplo de π/2

    con_rz = QuantumCircuit(2)
    con_rz.h(0)
    con_rz.rz(angulo, 0)
    con_rz.cx(0, 1)
    con_rz.measure_all()

    try:
        conteos_rz = conteos_stabilizer(con_rz)
        error_rz = None
        print(conteos_rz)
    except Exception as e:
        conteos_rz = None
        error_rz = e
        print("el simulador lo rechaza:", type(e).__name__)
    return con_rz, conteos_rz, error_rz


@app.cell(hide_code=True)
def _(con_rz, conteos_rz, error_rz, veredicto):
    veredicto(error_rz is None and conteos_rz is not None and "rz" in con_rz.count_ops(),
              "El circuito corre con `stabilizer` y sigue teniendo su `rz`: el ángulo ya es de Clifford.",
              "El simulador sigue rechazando el circuito, o quitaste la `rz`. Prueba un múltiplo de π/2.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la versión de Clifford de un circuito

    Así se verifica hardware: tomas un circuito que no puedes simular, lo conviertes en uno
    de Clifford y comparas. Escribe `a_clifford(params)`, que redondee cada ángulo al
    múltiplo de $\\pi/2$ **más cercano**. Luego simulamos un `efficient_su2` de 30 qubits
    con esos ángulos.
    """)
    return


@app.cell
def _(conteos_stabilizer, efficient_su2, np):
    def a_clifford(params):
        # ✏️ redondea cada ángulo al múltiplo de π/2 más cercano
        return np.asarray(params)

    base = efficient_su2(30)
    params = np.random.default_rng(7).uniform(0, 2 * np.pi, base.num_parameters)
    params_clifford = a_clifford(params)

    medido = base.copy()
    medido.measure_all()
    try:
        conteos_su2 = conteos_stabilizer(medido.assign_parameters(params_clifford))
        print(len(conteos_su2), "cadenas distintas de 30 bits")
    except Exception as e:
        conteos_su2 = None
        print("el simulador lo rechaza:", type(e).__name__)
    return a_clifford, conteos_su2, params, params_clifford


@app.cell(hide_code=True)
def _(conteos_su2, np, params, params_clifford, veredicto):
    _pasos = np.asarray(params_clifford) / (np.pi / 2)
    _cerca = np.abs(np.asarray(params_clifford) - params).max() <= np.pi / 4 + 1e-9
    veredicto(conteos_su2 is not None and np.allclose(_pasos, np.round(_pasos)) and _cerca,
              f"Los {len(params)} ángulos son múltiplos de π/2, ninguno se movió más de π/4, y 30 qubits se simulan sin problema.",
              "Todos los ángulos deben ser múltiplos de π/2 y quedar a menos de π/4 del original.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** redondear cambia el circuito, así que su resultado ya no es el del
    original. ¿Qué te dice sobre un QPU que reproduce bien la versión de Clifford?
    ¿Qué no te garantiza?
    """)
    return


if __name__ == "__main__":
    app.run()
