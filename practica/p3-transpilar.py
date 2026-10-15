import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.1 · Por qué hay que transpilar")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def es_isa_referencia(circuito, target):
        for inst in circuito.data:
            qargs = tuple(circuito.find_bit(q).index for q in inst.qubits)
            if not target.instruction_supported(inst.operation.name, qargs):
                return False
        return True

    backend = FakeFez()

    mo.md("""
    # 3.1 · Por qué hay que transpilar: práctica

    Tres misiones con el backend falso `FakeFez` (156 qubits, puertas base `cz`, `rz`, `sx`, `x`).
    No necesitas cuenta: todo corre en tu equipo. Busca el ✅ en cada una.
    """)
    return QuantumCircuit, backend, es_isa_referencia, generate_preset_pass_manager, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: los cuatro niveles

    Transpila una Hadamard y una Toffoli para `FakeFez` con cada nivel de optimización.
    Antes de ejecutar, predice: ¿tendrá el nivel 3 menos `cz` que el nivel 0? ¿Cuánto menos?
    """)
    return


@app.cell
def _(QuantumCircuit, backend, generate_preset_pass_manager):
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.ccx(0, 1, 2)

    tabla = {}
    for _nivel in range(4):
        _pm = generate_preset_pass_manager(_nivel, backend=backend, seed_transpiler=1)
        _isa = _pm.run(qc)
        tabla[_nivel] = (_isa.depth(), _isa.count_ops()["cz"])
        print(f"nivel {_nivel}: profundidad {_isa.depth()}, {tabla[_nivel][1]} CZ")
    return qc, tabla


@app.cell(hide_code=True)
def _(tabla, veredicto):
    veredicto(tabla[3][1] < tabla[0][1],
              f"El nivel 3 usa {tabla[3][1]} CZ frente a {tabla[0][1]} del nivel 0, y la profundidad baja de {tabla[0][0]} a {tabla[3][0]}.",
              "El nivel 3 debería usar menos CZ que el nivel 0. ¿Cambiaste el circuito?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: el pass manager al que le falta el backend

    Este pass manager no sabe nada del chip: devuelve el circuito casi intacto, con `h` y `ccx`,
    que `FakeFez` no ejecuta. Arréglalo con **un argumento** para que el resultado sea ISA.
    """)
    return


@app.cell
def _(backend, es_isa_referencia, generate_preset_pass_manager, qc):
    pm_corto = generate_preset_pass_manager(optimization_level=1, seed_transpiler=1)  # ✏️ ¿qué le falta?
    isa_corto = pm_corto.run(qc)
    print(sorted(isa_corto.count_ops()), "→ ISA:", es_isa_referencia(isa_corto, backend.target))
    return (isa_corto,)


@app.cell(hide_code=True)
def _(backend, es_isa_referencia, isa_corto, veredicto):
    veredicto(es_isa_referencia(isa_corto, backend.target),
              f"Ahora solo hay instrucciones del Target: {sorted(isa_corto.count_ops())}.",
              f"Siguen apareciendo instrucciones que el chip no ejecuta: {sorted(isa_corto.count_ops())}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un verificador ISA

    Escribe `es_isa(circuito, target)`: devuelve `True` si **cada** instrucción está en el `Target`
    y actúa sobre qubits donde el `Target` la admite (puertas base **y** conectividad).
    Pista: `target.instruction_supported(nombre, qargs)` responde por una instrucción;
    `circuito.find_bit(q).index` da el número de un qubit.
    """)
    return


@app.cell
def _():
    def es_isa(circuito, target):
        # ✏️ recorre circuito.data y pregunta al target por cada instrucción
        return False
    return (es_isa,)


@app.cell(hide_code=True)
def _(QuantumCircuit, backend, es_isa, generate_preset_pass_manager, qc, veredicto):
    _target = backend.target
    _aristas = set(_target.build_coupling_map().get_edges())
    _a, _b = sorted(_aristas)[0]
    _lejos = next(k for k in range(_target.num_qubits) if k != _a and (_a, k) not in _aristas and (k, _a) not in _aristas)

    _vecinos = QuantumCircuit(_target.num_qubits)
    _vecinos.cz(_a, _b)
    _lejanos = QuantumCircuit(_target.num_qubits)
    _lejanos.cz(_a, _lejos)
    _con_h = QuantumCircuit(_target.num_qubits)
    _con_h.h(_a)

    _isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
    _casos = [(_isa, True), (qc, False), (_vecinos, True), (_lejanos, False), (_con_h, False)]
    _fallos = [k for k, (c, esperado) in enumerate(_casos) if es_isa(c, _target) != esperado]
    veredicto(not _fallos,
              "Tu `es_isa` acepta el circuito transpilado y rechaza los que usan puertas o pares que el chip no tiene.",
              f"Tu `es_isa` se equivoca en {len(_fallos)} de {len(_casos)} casos de prueba: un circuito transpilado, el original, "
              "una `cz` entre vecinos, una `cz` entre qubits lejanos y una `h`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en el proyecto Ising cada paso de tiempo usa `rzz`, que `FakeFez` no tiene.
    ¿En qué puertas base crees que se convertirá, y cómo cambia eso la profundidad total?
    Lo medirás en el hito III.
    """)
    return


if __name__ == "__main__":
    app.run()
