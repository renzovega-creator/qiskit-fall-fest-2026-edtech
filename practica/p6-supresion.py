import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.2 · Supresión: desacoplamiento dinámico y twirling")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import CXGate, XGate
    from qiskit.quantum_info import Operator, Pauli
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 6.2 · Supresión: práctica

    Tres misiones sobre las dos técnicas de la lección, con un backend falso y sin cuenta.
    La idea común: **añadir operaciones que, en el caso ideal, no cambian nada**.
    Para comprobarlo usaremos la matriz del circuito: `Operator(a).equiv(Operator(b))`
    es verdadero cuando dos circuitos hacen lo mismo salvo una fase global.
    """)
    return (
        ALAPScheduleAnalysis,
        CXGate,
        Operator,
        PadDynamicalDecoupling,
        PassManager,
        Pauli,
        QuantumCircuit,
        XGate,
        FakeManilaV2,
        mo,
        np,
        transpile,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: pulsos en los huecos

    El circuito deja al qubit 2 esperando mientras los qubits 0 y 1 trabajan, y al qubit 0
    esperando al final. Programamos el circuito (`ALAPScheduleAnalysis`) y rellenamos los
    huecos con una secuencia **XX** (`PadDynamicalDecoupling`). Antes de ejecutar, apuesta:
    ¿cuántos pulsos X se añaden y cambia la operación del circuito?
    """)
    return


@app.cell
def _(ALAPScheduleAnalysis, FakeManilaV2, Operator, PadDynamicalDecoupling, PassManager, QuantumCircuit, XGate, transpile):
    fake = FakeManilaV2()
    logico = QuantumCircuit(3)
    logico.h(0)
    for _ in range(3):
        logico.cx(0, 1)
    logico.cx(1, 2)
    logico.h(2)
    isa = transpile(logico, fake, optimization_level=0, initial_layout=[0, 1, 2], seed_transpiler=1)

    def con_dd(secuencia):
        pm = PassManager([ALAPScheduleAnalysis(target=fake.target),
                          PadDynamicalDecoupling(target=fake.target, dd_sequence=secuencia)])
        return pm.run(isa)

    def pulsos_x(qc):
        return sum(1 for inst in qc.data if inst.operation.name == "x")

    con_xx = con_dd([XGate(), XGate()])
    print("pulsos X añadidos:", pulsos_x(con_xx) - pulsos_x(isa))
    print("misma operación:", Operator(isa).equiv(Operator(con_xx)))
    return con_dd, con_xx, fake, isa, pulsos_x


@app.cell(hide_code=True)
def _(con_xx, isa, Operator, pulsos_x, veredicto):
    veredicto(pulsos_x(con_xx) > pulsos_x(isa) and Operator(isa).equiv(Operator(con_xx)),
              "Se añadieron pulsos y la operación ideal es la misma: el desacoplamiento solo rellena esperas.",
              "Deberían aparecer pulsos X nuevos y el circuito seguir equivaliendo al original.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: una secuencia más larga

    Cambia la secuencia por **cuatro** pulsos X (también es la identidad). Tendrás el doble de
    pulsos en cada hueco: más protección contra la deriva lenta, pero cada pulso también
    puede fallar. La comprobación pide el doble de pulsos que con XX y la misma operación.
    """)
    return


@app.cell
def _(XGate, con_dd, isa, pulsos_x):
    secuencia = [XGate(), XGate()]   # ✏️ cuatro pulsos X
    con_secuencia = con_dd(secuencia)
    pulsos_secuencia = pulsos_x(con_secuencia) - pulsos_x(isa)
    pulsos_secuencia
    return con_secuencia, pulsos_secuencia, secuencia


@app.cell(hide_code=True)
def _(Operator, XGate, con_dd, con_secuencia, isa, pulsos_secuencia, pulsos_x, veredicto):
    _base = pulsos_x(con_dd([XGate(), XGate()])) - pulsos_x(isa)
    veredicto(pulsos_secuencia == 2 * _base and Operator(isa).equiv(Operator(con_secuencia)),
              f"{pulsos_secuencia} pulsos en total, el doble que con XX ({_base}), y el circuito sigue haciendo lo mismo.",
              f"Hay {pulsos_secuencia} pulsos; con cuatro X por hueco deberían ser {2 * _base}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: una variante de twirling

    El twirling de una CX pone una Pauli $P_L$ **antes** y otra $P_R$ **después**, de modo que el
    conjunto siga siendo la misma CX. Dada $P_L$, la Pauli que hay que poner después es la que
    sale de empujar $P_L$ a través de la CX: $P_R = \\mathrm{CX}\\,P_L\\,\\mathrm{CX}^\\dagger$.

    Completa `variante(rng)`: elige $P_L$ al azar y calcula `despues`.
    Pista: `Pauli.evolve(CXGate())` hace exactamente ese cambio.
    """)
    return


@app.cell
def _(CXGate, Pauli, QuantumCircuit, np):
    def variante(rng):
        antes = Pauli("".join(rng.choice(list("IXYZ"), 2)))
        despues = antes   # ✏️ la Pauli que mantiene la operación ideal
        qc = QuantumCircuit(2)
        qc.append(antes.to_instruction(), [0, 1])
        qc.cx(0, 1)
        qc.append(despues.to_instruction(), [0, 1])
        return qc
    return (variante,)


@app.cell(hide_code=True)
def _(CXGate, Operator, QuantumCircuit, np, variante, veredicto):
    _rng = np.random.default_rng(3)
    _cx = Operator(CXGate())
    _vars = [variante(_rng) for _ in range(40)]
    _iguales = sum(Operator(v).equiv(_cx) for v in _vars)
    _distintas = len({v.data[0].operation.params[0] for v in _vars})
    veredicto(_iguales == 40 and _distintas >= 8,
              f"Las 40 variantes equivalen a una CX y usan {_distintas} Paulis distintas antes de ella: la operación ideal se conserva, el ruido se reparte.",
              f"{_iguales} de 40 variantes equivalen a una CX. Revisa `despues`: debe cambiar según `antes`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el desacoplamiento y el twirling no cambian el resultado ideal. ¿Por qué
    entonces pueden cambiar el resultado que mides? ¿Y en qué circuito crees que *empeorarían*
    las cosas?
    """)
    return


if __name__ == "__main__":
    app.run()
