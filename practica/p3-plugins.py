import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.7 · Plugins del transpilador")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit.random import random_circuit
    from qiskit.quantum_info import Clifford, random_clifford
    from qiskit.synthesis import synth_clifford_bm
    from qiskit.transpiler import CouplingMap, PassManager, generate_preset_pass_manager
    from qiskit.transpiler.passes import HighLevelSynthesis
    from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig
    from qiskit.transpiler.passes.synthesis.plugin import (
        HighLevelSynthesisPlugin,
        high_level_synthesis_plugin_names,
        unitary_synthesis_plugin_names,
    )
    from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 3.7 · Plugins del transpilador: práctica

    Tres misiones: listar los plugins que ya trae Qiskit, elegir uno distinto para el routing
    y escribir tu propio plugin de síntesis de Clifford. Todo corre en local, sin instalar paquetes.
    """)
    return (
        Clifford,
        CouplingMap,
        HLSConfig,
        HighLevelSynthesis,
        HighLevelSynthesisPlugin,
        PassManager,
        QuantumCircuit,
        generate_preset_pass_manager,
        high_level_synthesis_plugin_names,
        list_stage_plugins,
        mo,
        random_circuit,
        random_clifford,
        synth_clifford_bm,
        unitary_synthesis_plugin_names,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: qué plugins hay

    Pregunta a Qiskit qué métodos tiene registrados para sintetizar un Clifford, para sintetizar
    una unitaria y para el routing. Antes de ejecutar, predice si `default` aparece en las listas.
    """)
    return


@app.cell
def _(high_level_synthesis_plugin_names, list_stage_plugins, unitary_synthesis_plugin_names):
    clifford_metodos = high_level_synthesis_plugin_names("clifford")
    unitaria_metodos = unitary_synthesis_plugin_names()
    routing_metodos = list_stage_plugins("routing")
    print("clifford:", clifford_metodos)
    print("unitaria:", unitaria_metodos)
    print("routing: ", routing_metodos)
    return clifford_metodos, routing_metodos, unitaria_metodos


@app.cell(hide_code=True)
def _(clifford_metodos, routing_metodos, unitaria_metodos, veredicto):
    veredicto("greedy" in clifford_metodos and "sabre" in routing_metodos and "default" in unitaria_metodos,
              f"Hay {len(clifford_metodos)} métodos para Clifford, {len(unitaria_metodos)} para unitarias y {len(routing_metodos)} para el routing; `default` está en todas.",
              "Faltan métodos conocidos en alguna lista.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: otro método de routing

    Un circuito aleatorio sobre una cuadrícula de 3×3 se transpila con `routing_method="basic"`,
    que inserta muchos SWAP. Cambia el método por otro de la lista del ejercicio anterior para
    que el resultado tenga **55 CNOT o menos**.
    """)
    return


@app.cell
def _(CouplingMap, generate_preset_pass_manager, random_circuit):
    cuadricula = CouplingMap.from_grid(3, 3)
    aleatorio = random_circuit(9, 6, max_operands=2, seed=3)
    metodo = "basic"  # ✏️ prueba otro método de routing
    pm_routing = generate_preset_pass_manager(
        2, coupling_map=cuadricula, basis_gates=["cx", "rz", "sx", "x"],
        routing_method=metodo, seed_transpiler=0)
    cx_routing = pm_routing.run(aleatorio).count_ops().get("cx", 0)
    print(metodo, "→", cx_routing, "CNOT")
    return cx_routing, metodo


@app.cell(hide_code=True)
def _(cx_routing, metodo, veredicto):
    veredicto(cx_routing <= 55,
              f"Con `{metodo}` bajas a {cx_routing} CNOT. Con `basic` eran 79.",
              f"Con `{metodo}` salen {cx_routing} CNOT; hace falta 55 o menos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: tu plugin de síntesis de Clifford

    Completa `MiClifford.run`: si el Clifford es de **3 qubits o menos**, devuelve el circuito de
    `synth_clifford_bm`; si es mayor, devuelve `None` para que el transpilador pruebe el siguiente
    método. La comprobación lo usa con `HLSConfig`, solo y seguido de `"greedy"`.
    """)
    return


@app.cell
def _(HighLevelSynthesisPlugin, synth_clifford_bm):
    class MiClifford(HighLevelSynthesisPlugin):
        def run(self, high_level_object, coupling_map=None, target=None, qubits=None, **options):
            return None  # ✏️ sintetiza con synth_clifford_bm si num_qubits <= 3
    return (MiClifford,)


@app.cell(hide_code=True)
def _(Clifford, HLSConfig, HighLevelSynthesis, MiClifford, PassManager, QuantumCircuit, random_clifford, veredicto):
    def _sintetiza(cl, metodos):
        _qc = QuantumCircuit(cl.num_qubits)
        _qc.append(cl, range(cl.num_qubits))
        _config = HLSConfig(clifford=metodos)
        return PassManager([HighLevelSynthesis(hls_config=_config)]).run(_qc)

    _cl3, _cl4 = random_clifford(3, seed=1), random_clifford(4, seed=1)
    _pequeno = _sintetiza(_cl3, [(MiClifford(), {})])
    _grande = _sintetiza(_cl4, [(MiClifford(), {})])
    _con_respaldo = _sintetiza(_cl4, [(MiClifford(), {}), "greedy"])
    _bien_pequeno = "clifford" not in _pequeno.count_ops() and Clifford(_pequeno) == _cl3
    _bien_grande = _grande.count_ops().get("clifford") == 1
    _bien_respaldo = "clifford" not in _con_respaldo.count_ops()
    veredicto(_bien_pequeno and _bien_grande and _bien_respaldo,
              "Con 3 qubits tu plugin sintetiza y el circuito es equivalente; con 4 devuelve `None` y el Clifford queda intacto, hasta que `greedy` lo recoge como respaldo.",
              f"Clifford de 3 qubits sintetizado y equivalente: {_bien_pequeno}; de 4 qubits sin tocar: {_bien_grande}; con respaldo `greedy` sintetizado: {_bien_respaldo}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué ganas escribiendo un plugin en lugar de un pase suelto?
    En el hito III compararás niveles de optimización y profundidad sobre el circuito Ising en `FakeFez`.
    """)
    return


if __name__ == "__main__":
    app.run()
