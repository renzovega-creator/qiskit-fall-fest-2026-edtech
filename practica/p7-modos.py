import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.7 · Modos de ejecución")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import Batch
    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeBelemV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    mo.md("""
    # 7.7 · Modos de ejecución: práctica

    Tres misiones sobre lotes y sesiones. Se ejecutan con `FakeBelemV2` en el modo de prueba
    local: la sintaxis es la real, pero los modos se ignoran, así que no necesitas cuenta.
    Busca el ✅ en cada una.
    """)
    return Batch, QuantumCircuit, Sampler, backend, mo, np, pm, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: tres trabajos en un lote

    Abre un `Batch`, envía tres trabajos y recoge sus conteos. **Antes de ejecutar, predice**
    qué imprime `lote.details()` en modo local.
    """)
    return


@app.cell
def _(Batch, QuantumCircuit, Sampler, backend, pm):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()
    isa_bell = pm.run(bell)

    with Batch(backend=backend, max_time="25m") as lote:
        sampler = Sampler(mode=lote)
        trabajos_bell = [sampler.run([isa_bell]) for _ in range(3)]
        disparos = [sum(j.result()[0].data.meas.get_counts().values()) for j in trabajos_bell]

    print(len(trabajos_bell), "trabajos con", disparos, "disparos")
    print("details():", lote.details())
    return (disparos,)


@app.cell(hide_code=True)
def _(disparos, veredicto):
    veredicto(len(disparos) == 3 and all(d == 4096 for d in disparos),
              "Tres trabajos con 4096 disparos cada uno. En local `details()` no devuelve nada: los modos se ignoran.",
              "Deberían ser tres trabajos de 4096 disparos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: partir una lista larga en trabajos

    Hay 20 circuitos en una lista. Un lote aprovecha el preprocesamiento en paralelo si los
    repartes en **5 trabajos de 4 circuitos**. Cambia `trozos` para que sea una lista de 5
    listas, sin perder ni repetir ningún circuito.
    """)
    return


@app.cell
def _(Batch, QuantumCircuit, Sampler, backend, np, pm):
    circuitos = []
    for _angulo in np.linspace(0, np.pi, 20):
        _qc = QuantumCircuit(2)
        _qc.rx(_angulo, 0)
        _qc.cx(0, 1)
        _qc.measure_all()
        circuitos.append(pm.run(_qc))

    trozos = [circuitos]   # ✏️ 5 listas de 4 circuitos

    with Batch(backend=backend) as lote_grande:
        _sampler = Sampler(mode=lote_grande)
        _trabajos = [_sampler.run(_t) for _t in trozos]
        ejecutados = sum(len(_j.result()) for _j in _trabajos)
    print(len(trozos), "trabajos ·", ejecutados, "circuitos ejecutados")
    return circuitos, ejecutados, trozos


@app.cell(hide_code=True)
def _(circuitos, ejecutados, trozos, veredicto):
    _sin_repetir = sorted(id(c) for t in trozos for c in t) == sorted(id(c) for c in circuitos)
    veredicto(len(trozos) == 5 and _sin_repetir and all(len(t) == 4 for t in trozos) and ejecutados == 20,
              "Cinco trabajos de 4 circuitos: los 20 se ejecutan una sola vez.",
              f"Hay {len(trozos)} trabajos de tamaños {[len(t) for t in trozos]}; deben ser 5 de 4, "
              f"y se ejecutaron {ejecutados} circuitos de 20.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: elegir el modo

    Escribe `elegir_modo(n_trabajos, entradas_listas, iterativo, minutos_qpu, plan)`, que
    devuelva la tupla `(modo, juntar)` según las recomendaciones de la lección:

    - un solo trabajo: `"job"`;
    - si la carga es iterativa o no tiene todas las entradas listas al principio:
      `"session"`, salvo en el plan `"open"`, que no admite sesiones: ahí, `"job"`;
    - en cualquier otro caso: `"batch"`;
    - `juntar` es `True` si hay varios trabajos y cada uno usa menos de 1 minuto de QPU
      (conviene unirlos en uno mayor); si no, `False`.
    """)
    return


@app.cell
def _():
    def elegir_modo(n_trabajos, entradas_listas, iterativo, minutos_qpu, plan="pago"):
        return ("batch", False)   # ✏️ tu código aquí
    return (elegir_modo,)


@app.cell(hide_code=True)
def _(elegir_modo, veredicto):
    _casos = [
        ((1, True, False, 5, "pago"), ("job", False)),
        ((1, True, False, 0.5, "pago"), ("job", False)),
        ((6, True, False, 3, "pago"), ("batch", False)),
        ((30, True, False, 0.2, "pago"), ("batch", True)),
        ((40, False, True, 2, "pago"), ("session", False)),
        ((8, False, False, 2, "pago"), ("session", False)),
        ((40, False, True, 2, "open"), ("job", False)),
        ((6, True, False, 3, "open"), ("batch", False)),
    ]
    _fallos = [f"{args} → {elegir_modo(*args)} (esperado {esperado})"
               for args, esperado in _casos if elegir_modo(*args) != esperado]
    veredicto(not _fallos,
              f"`elegir_modo` acierta en los {len(_casos)} casos.",
              "Falla en: " + "; ".join(_fallos))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en tu proyecto Ising quieres comparar varios números de pasos de Trotter
    con las mismas entradas, y después repetir con mitigación. ¿Qué modo elegirías para cada
    parte y por qué?
    """)
    return


if __name__ == "__main__":
    app.run()
