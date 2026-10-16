import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.6 · Plantillas de Qiskit Functions")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Una plantilla de Qiskit Functions se despliega en Serverless y pide una cuenta. Esta es
    # una versión local con la misma estructura: validar, construir, ejecutar. El backend
    # `statevector` es exacto; `fake` simula el ruido de un dispositivo. `runtime` necesita un QPU.
    COSTE = {"etapas": 0}

    def validar(entradas):
        faltan = [k for k in ("n", "t_steps") if k not in entradas]
        if faltan:
            raise ValueError(f"faltan entradas: {faltan}")
        if not isinstance(entradas["t_steps"], int) or entradas["t_steps"] < 1:
            raise ValueError("t_steps debe ser un entero positivo")

    def construir(entradas):
        """Etapa cara en una función real (aquí solo la contamos): un circuito por paso de tiempo."""
        COSTE["etapas"] += 1
        n, J, h, dt = entradas["n"], entradas.get("J", 1.0), entradas.get("h", 0.5), entradas.get("dt", 0.2)
        circuitos = []
        for k in range(entradas["t_steps"] + 1):
            qc = QuantumCircuit(n)
            for _ in range(k):
                for a in range(0, n - 1, 2):
                    qc.rzz(2 * J * dt, a, a + 1)
                for a in range(1, n - 1, 2):
                    qc.rzz(2 * J * dt, a, a + 1)
                for a in range(n):
                    qc.rx(2 * h * dt, a)
            circuitos.append(qc)
        return circuitos

    def ejecutar(circuitos, entradas, backend):
        n = entradas["n"]
        magnetizacion = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
        if backend == "statevector":
            r = StatevectorEstimator().run([(c, magnetizacion) for c in circuitos]).result()
            valores = [float(x.data.evs) for x in r]
        elif backend == "fake":
            fake = FakeBelemV2()
            pm = generate_preset_pass_manager(optimization_level=1, backend=fake, seed_transpiler=1)
            est = AerEstimator.from_backend(fake, options={"backend_options": {"seed_simulator": 3}})
            pubs = []
            for c in circuitos:
                isa = pm.run(c)
                pubs.append((isa, magnetizacion.apply_layout(isa.layout)))
            valores = [float(x.data.evs) for x in est.run(pubs, precision=0.02).result()]
        else:
            raise ValueError("backend debe ser 'statevector' o 'fake'")
        return {"times": [k * entradas.get("dt", 0.2) for k in range(len(circuitos))], "magnetizacion": valores}

    def simular(entradas, backend="statevector"):
        validar(entradas)
        return ejecutar(construir(entradas), entradas, backend)

    mo.md("""
    # 8.6 · Plantillas de Qiskit Functions: práctica

    Las plantillas siguen unas buenas prácticas: validar las entradas al principio y probar
    en simuladores antes del QPU. Tres misiones sobre una función de simulación de una cadena
    de espines, con los backends `statevector` y `fake` en tu equipo. Busca el ✅ en cada una.
    """)
    return COSTE, construir, ejecutar, mo, np, simular, validar, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el mismo código en dos backends

    Ejecuta la función con `statevector` (exacto) y con `fake` (ruido de un dispositivo
    simulado). Devuelve la magnetización media $\\langle Z\\rangle$ en cada instante.
    """)
    return


@app.cell
def _(simular):
    entradas = dict(n=4, t_steps=3, J=1.0, h=0.5, dt=0.2)
    exacto = simular(entradas, "statevector")
    ruidoso = simular(entradas, "fake")
    for t, a, b in zip(exacto["times"], exacto["magnetizacion"], ruidoso["magnetizacion"]):
        print(f"t = {t:.1f}   exacto {a:+.3f}   con ruido {b:+.3f}")
    return exacto, ruidoso


@app.cell(hide_code=True)
def _(exacto, np, ruidoso, veredicto):
    _a, _b = np.array(exacto["magnetizacion"]), np.array(ruidoso["magnetizacion"])
    veredicto(len(_a) == 4 and abs(_a[0] - 1) < 1e-9 and 0 < np.max(np.abs(_a - _b)) < 0.25,
              "Mismo código, dos backends: el ruido separa un poco la curva de la exacta.",
              "Espero 4 instantes, magnetización 1 en t = 0 y una diferencia pequeña pero no nula con ruido.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: validar al principio

    `mi_funcion` valida las entradas **después** de la etapa cara. Si una entrada es inválida, gastas
    el recurso para nada. Reordénala para que valide primero.
    """)
    return


@app.cell
def _(construir, ejecutar, validar):
    def mi_funcion(entradas, backend="statevector"):
        circuitos = construir(entradas)        # etapa cara
        validar(entradas)                      # ✏️ muévela antes de la etapa cara
        return ejecutar(circuitos, entradas, backend)
    return (mi_funcion,)


@app.cell(hide_code=True)
def _(COSTE, mi_funcion, veredicto):
    COSTE["etapas"] = 0
    try:
        mi_funcion({"n": 4, "t_steps": 0})   # t_steps inválido
        _error = None
    except ValueError as e:
        _error = str(e)
    _gastadas = COSTE["etapas"]
    veredicto(_error is not None and _gastadas == 0,
              f"Falla enseguida ({_error}) y no se gastó ninguna etapa cara.",
              f"Falló con «{_error}» pero ya se habían ejecutado {_gastadas} etapa(s) cara(s)."
              if _error else "Debería lanzar `ValueError` con una entrada inválida.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: cuánto cuesta el plan de compresión

    La plantilla AQC + Trotter recibe un plan `{"n_steps": k, "ansatz_steps": m}`: comprime `k`
    pasos de Trotter en un ansatz construido como `m` pasos, y los pasos restantes se
    ejecutan sin comprimir. Escribe `pasos_en_qpu(t_steps, plan)`: las capas de Trotter del
    circuito del último paso, es decir, `m` más los pasos sin comprimir. Si el plan comprime
    más pasos de los que hay, lanza `ValueError`: es la validación temprana de la lección.
    """)
    return


@app.cell
def _():
    def pasos_en_qpu(t_steps, plan):
        # ✏️ capas del ansatz + pasos sin comprimir; ValueError si n_steps > t_steps
        return None
    return (pasos_en_qpu,)


@app.cell(hide_code=True)
def _(pasos_en_qpu, veredicto):
    def _lanza():
        try:
            pasos_en_qpu(3, {"n_steps": 5, "ansatz_steps": 2})
        except ValueError:
            return True
        return False

    _casos = {(10, 6, 2): 6, (8, 5, 1): 4, (4, 4, 1): 1}
    _r = {c: pasos_en_qpu(c[0], {"n_steps": c[1], "ansatz_steps": c[2]}) for c in _casos}
    veredicto(_r == _casos and _lanza(),
              "Comprimir 6 de 10 pasos en un ansatz de 2 deja 6 capas: 4 menos que sin comprimir.",
              f"Tu función da {_r}. Espero {_casos}, y `ValueError` si el plan no cabe en `t_steps`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué fallos de tu función de la misión 🟡 descubrirías con `statevector` antes
    de gastar tiempo de QPU, y cuáles solo con `fake`?
    """)
    return


if __name__ == "__main__":
    app.run()
