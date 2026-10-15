import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.6 · Pruebas locales")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit.circuit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""

    Tres misiones con las primitivas del lado del cliente, que corren en tu equipo con un
    backend falso o con Aer. Busca el ✅ en cada una.
    """)
    return (
        AerSimulator,
        Estimator,
        FakeManilaV2,
        QuantumCircuit,
        Sampler,
        SparsePauliOp,
        generate_preset_pass_manager,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un Bell en un backend falso

    `FakeManilaV2` imita un procesador real de 5 qubits con su ruido. Antes de ejecutar,
    predice: ¿aparecerán `01` y `10`? ¿Cuántos disparos hará el Sampler por defecto?
    """)
    return


@app.cell
def _(FakeManilaV2, QuantumCircuit, Sampler, generate_preset_pass_manager):
    fake_manila = FakeManilaV2()

    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell_medido = bell.copy()
    bell_medido.measure_all()

    isa_bell = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(bell_medido)
    sampler_fake = Sampler(mode=fake_manila, options={"simulator": {"seed_simulator": 42}})
    conteos_fake = sampler_fake.run([isa_bell]).result()[0].data.meas.get_counts()
    print(conteos_fake)
    return bell, conteos_fake, fake_manila


@app.cell(hide_code=True)
def _(conteos_fake, veredicto):
    _total = sum(conteos_fake.values())
    _raros = conteos_fake.get("01", 0) + conteos_fake.get("10", 0)
    veredicto(_total == 4096 and 0 < _raros < 0.1 * _total,
              f"{_total} disparos por defecto, y {_raros} en `01` o `10`: el ruido de la instantánea del QPU.",
              "Deberían ser 4096 disparos, con algunos `01` o `10` pero menos del 10 %.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: quita el ruido

    Para depurar la lógica de un programa a veces conviene un simulador ideal. Cambia
    `backend` por `AerSimulator()` y deja el resto igual: el programa no cambia, solo el
    backend. Fíjate en que ya no aparecen `01` ni `10`.
    """)
    return


@app.cell
def _(
    AerSimulator,
    Sampler,
    bell_medido,
    fake_manila,
    generate_preset_pass_manager,
):
    backend = fake_manila   # ✏️ cambia a AerSimulator()

    isa_local = generate_preset_pass_manager(backend=backend, optimization_level=1).run(bell_medido)
    sampler_local = Sampler(mode=backend, options={"simulator": {"seed_simulator": 42}})
    conteos_local = sampler_local.run([isa_local]).result()[0].data.meas.get_counts()
    print(type(backend).__name__, conteos_local)
    return backend, conteos_local


@app.cell(hide_code=True)
def _(AerSimulator, backend, conteos_local, veredicto):
    veredicto(isinstance(backend, AerSimulator) and set(conteos_local) == {"00", "11"},
              "Sin ruido solo salen `00` y `11`: el mismo código, otro backend.",
              "Todavía salen otras cadenas. Cambia `backend` por `AerSimulator()`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: prueba la mitigación antes de usar un QPU

    Con las primitivas del lado del cliente, la mitigación de errores de lectura corre en
    local. Completa `ev_zz(mitigar)`, que estima $\\langle ZZ\\rangle$ del estado de Bell con un
    Estimator sobre `fake_manila`, activando `resilience.measure_mitigation` según el
    argumento. El valor ideal es 1: la versión mitigada debe acercarse más.
    """)
    return


@app.cell
def _(
    Estimator,
    SparsePauliOp,
    bell,
    fake_manila,
    generate_preset_pass_manager,
):
    isa_estado = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(bell)
    zz = SparsePauliOp("ZZ").apply_layout(isa_estado.layout)

    def ev_zz(mitigar):
        estimator = Estimator(mode=fake_manila, options={"simulator": {"seed_simulator": 1}})
        # ✏️ activa o desactiva estimator.options.resilience.measure_mitigation según `mitigar`
        return float(estimator.run([(isa_estado, zz)]).result()[0].data.evs)

    sin_mitigar = ev_zz(False)
    mitigado = ev_zz(True)
    print(f"sin mitigar {sin_mitigar:.3f} · mitigado {mitigado:.3f}")
    return mitigado, sin_mitigar


@app.cell(hide_code=True)
def _(mitigado, sin_mitigar, veredicto):
    veredicto(abs(1 - mitigado) < abs(1 - sin_mitigar) - 0.02,
              f"La mitigación acerca el valor a 1: de {sin_mitigar:.3f} a {mitigado:.3f}.",
              "El valor mitigado no es mejor que el otro. ¿Activaste `measure_mitigation` según `mitigar`?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** la mitigación mejoró el resultado, pero también costó más tiempo y
    memoria. ¿Qué tamaño de circuito te dejaría de permitir probarla en local?
    """)
    return


if __name__ == "__main__":
    app.run()
