import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="9.1 · Integrar recursos cuánticos externos")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter, Measure
    from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
    from qiskit.primitives import BackendSamplerV2
    from qiskit.providers import BackendV2, Options
    from qiskit.providers.basic_provider import BasicSimulator
    from qiskit.transpiler import Target, InstructionProperties, generate_preset_pass_manager

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 9.1 · Integrar recursos cuánticos externos: práctica

    Un proveedor necesita dos piezas: un `BackendV2` con su `Target` para transpilar, y
    una forma de ejecutar. En estas tres misiones construyes ambas para un QPU
    imaginario de tres qubits en línea. Nada necesita cuenta ni red.
    """)
    return (
        BackendSamplerV2,
        BackendV2,
        BasicSimulator,
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
        generate_preset_pass_manager,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un `BackendV2` mínimo

    Ejecuta la clase de la lección. Su `Target` dice qué puertas existen, en qué qubits y
    con qué error; la CZ solo une los pares `(0, 1)` y `(1, 2)`. Lee cada línea antes de
    seguir.
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
    RZGate,
    SXGate,
    Target,
    XGate,
):
    class MiQPU(BackendV2):
        def __init__(self):
            super().__init__(name="mi_qpu")
            self._target = Target(num_qubits=3)
            theta = Parameter("θ")
            for gate in (RZGate(theta), SXGate(), XGate(), Measure()):
                self._target.add_instruction(gate, {(q,): InstructionProperties(error=1e-4) for q in range(3)})
            self._target.add_instruction(CZGate(), {(0, 1): InstructionProperties(error=1e-2),
                                                    (1, 2): InstructionProperties(error=1e-2)})

        @property
        def target(self):
            return self._target

        @property
        def max_circuits(self):
            return None

        @classmethod
        def _default_options(cls):
            return Options(shots=1024)

        def run(self, run_input, **options):
            raise NotImplementedError("aquí se enviaría el trabajo al servicio")

    backend = MiQPU()
    backend.operation_names, backend.coupling_map.get_edges()
    return MiQPU, backend


@app.cell
def _(QuantumCircuit, backend, generate_preset_pass_manager):
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 2)
    isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
    ops = dict(isa.count_ops())
    ops
    return ops, qc


@app.cell(hide_code=True)
def _(ops, veredicto):
    veredicto(ops.get("cz") == 1 and "swap" not in ops,
              "La CNOT entre los qubits 0 y 2 se tradujo a una sola CZ, sin SWAP: el transpilador eligió qubits vecinos.",
              f"Salió {ops}. Debería haber una CZ y ningún SWAP. ¿Cambiaste el `Target`?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: duraciones en el `Target`

    El `Target` también guarda cuánto dura cada instrucción. Con duraciones, Qiskit puede
    estimar cuánto dura un circuito. En `MiQPUDurable` asigna estas duraciones, en segundos:

    - `rz`, `sx`, `x` y `measure`, en los tres qubits: `5e-8`
    - `cz`, en `(0, 1)` y `(1, 2)`: `3e-7`

    Pista: `Target.update_instruction_properties(nombre, qargs, propiedades)` reemplaza las
    propiedades de una instrucción; conserva el `error` y añade `duration=...` en un
    `InstructionProperties`. Los errores son `1e-4` para las puertas de un qubit y `1e-2`
    para la CZ.
    """)
    return


@app.cell
def _(InstructionProperties, MiQPU):
    class MiQPUDurable(MiQPU):
        def __init__(self):
            super().__init__()
            # ✏️ asigna las duraciones en self._target

    durable = MiQPUDurable()
    return (durable,)


@app.cell(hide_code=True)
def _(durable, generate_preset_pass_manager, qc, veredicto):
    try:
        _isa = generate_preset_pass_manager(1, backend=durable, seed_transpiler=1).run(qc)
        _duracion = _isa.estimate_duration(durable.target)
        _ok = abs(_duracion - 6e-7) < 1e-9
        _no = f"La duración estimada es {_duracion:.3g} s y debería ser 6e-07 s. Revisa las duraciones que asignaste."
    except Exception as e:
        _ok, _no = False, f"Todavía no se puede estimar la duración ({type(e).__name__}): faltan duraciones en el `Target`."
    veredicto(_ok,
              "El circuito dura 6e-07 s: Qiskit suma las duraciones del camino más largo.",
              _no)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: ejecutar con una primitiva

    Un proveedor real enviaría el trabajo a su servicio. Aquí lo simulas: implementa `run`
    en `MiQPUSimulado` delegando en `BasicSimulator().run(run_input, **options)`, que viene
    con Qiskit. Así `BackendSamplerV2` convierte tu backend en un `Sampler`.
    """)
    return


@app.cell
def _(BasicSimulator, MiQPU):
    class MiQPUSimulado(MiQPU):
        def run(self, run_input, **options):
            raise NotImplementedError("✏️ delega en BasicSimulator")

    simulado = MiQPUSimulado()
    return (simulado,)


@app.cell
def _(BackendSamplerV2, QuantumCircuit, generate_preset_pass_manager, simulado):
    ghz = QuantumCircuit(3)
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(1, 2)
    ghz.measure_all()
    isa_ghz = generate_preset_pass_manager(1, backend=simulado, seed_transpiler=1).run(ghz)
    sampler = BackendSamplerV2(backend=simulado, options={"default_shots": 500})
    return isa_ghz, sampler


@app.cell(hide_code=True)
def _(isa_ghz, sampler, veredicto):
    try:
        _conteos = sampler.run([isa_ghz]).result()[0].data.meas.get_counts()
        _ok = set(_conteos) == {"000", "111"}
        _no = f"Salieron {sorted(_conteos)}; un GHZ solo da `000` y `111`."
    except NotImplementedError as e:
        _conteos, _ok, _no = {}, False, f"`run` todavía no ejecuta nada: {e}"
    veredicto(_ok,
              f"Tu proveedor ejecuta con `BackendSamplerV2`: {dict(sorted(_conteos.items()))}.",
              _no)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `BackendSamplerV2` no transpila: espera un circuito ya escrito con las
    puertas del `Target`. ¿Qué parte del trabajo es de tu backend y cuál del transpilador?
    """)
    return


if __name__ == "__main__":
    app.run()
