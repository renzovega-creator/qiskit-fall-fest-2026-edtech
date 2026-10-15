import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="3.4 · Representar un computador cuántico: Target")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit import Measure, Parameter
    from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
    from qiskit.providers import BackendV2, Options
    from qiskit.transpiler import InstructionProperties, Target, generate_preset_pass_manager

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 3.4 · Representar un computador cuántico: práctica

    Tres misiones con dispositivos inventados. No hay chip real: lo único que sabe el transpilador
    es lo que escribas en el `Target`. Busca el ✅ en cada una.
    """)
    return (
        CZGate,
        InstructionProperties,
        Measure,
        Parameter,
        QuantumCircuit,
        RZGate,
        SXGate,
        Target,
        XGate,
        BackendV2,
        Options,
        generate_preset_pass_manager,
        mo,
        transpile,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un backend propio

    Una cadena de 3 qubits con `rz`, `sx`, `x`, `cz` y medición. Pide una CX entre los qubits 0 y 2,
    que no son vecinos en la cadena, y mira en qué puertas la traduce el transpilador.
    Antes de ejecutar, predice: ¿aparecerá `swap`? ¿Y `x`?
    """)
    return


@app.cell
def _(
    BackendV2,
    CZGate,
    InstructionProperties,
    Measure,
    Options,
    Parameter,
    QuantumCircuit,
    RZGate,
    SXGate,
    Target,
    XGate,
    transpile,
):
    class MiBackend(BackendV2):
        def __init__(self):
            super().__init__(name="mi_backend")
            self._target = Target("cadena de 3", num_qubits=3)
            self._target.add_instruction(RZGate(Parameter("t")),
                {(q,): InstructionProperties(error=0.0, duration=0.0) for q in range(3)})
            for gate in (XGate(), SXGate(), Measure()):
                self._target.add_instruction(gate, {(q,): None for q in range(3)})
            self._target.add_instruction(CZGate(),
                {(0, 1): InstructionProperties(error=5e-3), (1, 2): InstructionProperties(error=5e-3)})

        @property
        def target(self):
            return self._target

        @property
        def max_circuits(self):
            return None

        @classmethod
        def _default_options(cls):
            return Options(shots=1024)

        def run(self, circuit, **kwargs):
            raise NotImplementedError

    cx_lejana = QuantumCircuit(3)
    cx_lejana.h(0)
    cx_lejana.cx(0, 2)
    puertas_isa = sorted(transpile(cx_lejana, MiBackend(), seed_transpiler=1).count_ops())
    puertas_isa
    return (puertas_isa,)


@app.cell(hide_code=True)
def _(puertas_isa, veredicto):
    veredicto(puertas_isa == ["cz", "rz", "sx"],
              "Sin SWAP: el transpilador puso los qubits en dos contiguos y tradujo la CX a una `cz` y puertas de un qubit. Todo salió del `Target`.",
              f"Salieron {puertas_isa}; deberían ser solo `cz`, `rz` y `sx`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: evitar un par averiado

    Este chip es un anillo de 4 qubits. En la tabla de calibración, el par (1, 2) figura con un
    error bajísimo, pero tú sabes que está averiado. El transpilador no lo sabe: fíate de la tabla
    y usa justo ese par. Cambia el diccionario para que **nunca** lo use.
    """)
    return


@app.cell
def _(
    CZGate,
    InstructionProperties,
    Measure,
    Parameter,
    QuantumCircuit,
    RZGate,
    SXGate,
    Target,
    XGate,
    generate_preset_pass_manager,
):
    errores_cz = {
        (0, 1): 5e-3,
        (1, 2): 1e-4,   # ✏️ este par está averiado
        (2, 3): 5e-3,
        (3, 0): 5e-3,
    }

    anillo = Target("anillo de 4", num_qubits=4)
    anillo.add_instruction(RZGate(Parameter("t")), {(q,): InstructionProperties(error=0.0, duration=0.0) for q in range(4)})
    for _puerta in (XGate(), SXGate(), Measure()):
        anillo.add_instruction(_puerta, {(q,): None for q in range(4)})
    anillo.add_instruction(CZGate(), {par: InstructionProperties(error=e) for par, e in errores_cz.items()})

    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    isa_anillo = generate_preset_pass_manager(3, target=anillo, seed_transpiler=1).run(bell)
    pares_usados = [tuple(sorted(isa_anillo.find_bit(q).index for q in i.qubits)) for i in isa_anillo.data if i.operation.num_qubits == 2]
    pares_usados
    return anillo, pares_usados


@app.cell(hide_code=True)
def _(anillo, pares_usados, veredicto):
    veredicto(bool(pares_usados) and (1, 2) not in pares_usados and not anillo.instruction_supported("cz", (1, 2)),
              f"El transpilador usa ahora {pares_usados}: como el par no está en el `Target`, nunca lo elige.",
              f"Sigue usando {pares_usados} o el par (1, 2) aún está en el `Target`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un `Target` para cadenas de cualquier tamaño

    Escribe `cadena(n)`: un `Target` de `n` qubits con `rz`, `sx`, `x` y `measure` en cada qubit,
    y `cz` **solo** entre vecinos (0–1, 1–2…). La comprobación transpila un GHZ de 3 a 6 qubits y
    exige que no haga falta ningún SWAP.
    """)
    return


@app.cell
def _(CZGate, InstructionProperties, Measure, Parameter, RZGate, SXGate, Target, XGate):
    def cadena(n):
        target = Target(f"cadena de {n}", num_qubits=n)
        target.add_instruction(RZGate(Parameter("t")), {(q,): None for q in range(n)})
        # ✏️ añade `sx`, `x` y `measure` en todos los qubits
        # ✏️ añade `cz` solo entre vecinos: (0, 1), (1, 2)…
        return target
    return (cadena,)


@app.cell(hide_code=True)
def _(QuantumCircuit, cadena, generate_preset_pass_manager, veredicto):
    def _prueba(n):
        ghz = QuantumCircuit(n)
        ghz.h(0)
        for k in range(n - 1):
            ghz.cx(k, k + 1)
        ghz.measure_all()
        target = cadena(n)
        isa = generate_preset_pass_manager(1, target=target, seed_transpiler=1).run(ghz)
        nombres = set(isa.count_ops()) - {"barrier"}
        cadena_ok = {frozenset(e) for e in target.build_coupling_map().get_edges()} == {frozenset((k, k + 1)) for k in range(n - 1)}
        return cadena_ok and nombres <= {"cz", "rz", "sx", "x", "measure"} and "cz" in nombres

    _malos = []
    for _n in range(3, 7):
        try:
            if not _prueba(_n):
                _malos.append(_n)
        except Exception:
            _malos.append(_n)
    veredicto(not _malos,
              "Tu `cadena(n)` sirve para n = 3…6: el GHZ se transpila solo con `cz`, `rz`, `sx`, `x` y mediciones, sin SWAP.",
              f"Falla para n = {_malos}. Revisa que estén `sx`, `x`, `measure` y que `cz` conecte solo a vecinos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** quitar un par del `Target` lo prohíbe para todos los circuitos. ¿Qué pasa si quitas
    demasiados? ¿Cómo lo notaría el transpilador, y qué te diría?
    """)
    return


if __name__ == "__main__":
    app.run()
