import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.3 · Primitivas de IBM y sus opciones")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    from qiskit_ibm_runtime.options_models import EstimatorOptions

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    isa_bell = pm.run(bell)
    zz = SparsePauliOp("ZZ").apply_layout(isa_bell.layout)

    def medir_zz(estimator):
        """⟨ZZ⟩ del estado de Bell y su error estándar, con la primitiva que recibe."""
        estimator.options.simulator.seed_simulator = 7
        datos = estimator.run([(isa_bell, zz)]).result()[0].data
        return float(datos.evs), float(datos.stds)

    mo.md("""

    Tres misiones con el `Estimator` del lado del cliente sobre `FakeManilaV2`, un procesador
    falso de 5 qubits. No necesitas cuenta. Busca el ✅ en cada misión.
    """)
    return Estimator, EstimatorOptions, backend, medir_zz, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: cuatro formas de fijar una opción

    Las cuatro dejan `default_precision` en $0{,}02$. Antes de ejecutar, predice: ¿cuánto valdrá
    `default_precision` en un `Estimator` al que **no** le fijaste nada?
    """)
    return


@app.cell
def _(Estimator, EstimatorOptions, backend):
    por_clase = Estimator(mode=backend, options=EstimatorOptions(default_precision=0.02))
    por_dict = Estimator(mode=backend, options={"default_precision": 0.02})

    por_atributo = Estimator(mode=backend)
    por_atributo.options.default_precision = 0.02

    por_update = Estimator(mode=backend)
    por_update.options.update(default_precision=0.02)

    sin_tocar = Estimator(mode=backend)

    precisiones = [e.options.default_precision for e in (por_clase, por_dict, por_atributo, por_update)]
    print("cuatro formas:", precisiones)
    print("sin tocar:", sin_tocar.options.default_precision, "· default_shots:", sin_tocar.options.default_shots)
    return (precisiones,)


@app.cell(hide_code=True)
def _(precisiones, veredicto):
    veredicto(precisiones == [0.02] * 4,
              "Las cuatro formas producen la misma opción. Sin tocar nada, la primitiva usa su valor por defecto.",
              f"Las cuatro deberían dar 0.02; dieron {precisiones}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: la primitiva copia las opciones

    Al crear el `Estimator`, copia el diccionario de opciones. Cambiar `opts` **después** no
    afecta al estimator: la última línea no hace nada útil. Cámbiala para que `est` use
    5000 disparos, y comprueba que el error baja.
    """)
    return


@app.cell
def _(Estimator, backend, medir_zz):
    opts = {"default_shots": 100}
    est = Estimator(mode=backend, options=opts)
    opts["default_shots"] = 5000   # ✏️ ¿a qué objeto hay que cambiárselo?

    _, error = medir_zz(est)
    print("default_shots =", est.options.default_shots, "· error de ⟨ZZ⟩ =", round(error, 4))
    return error, est


@app.cell(hide_code=True)
def _(error, est, veredicto):
    veredicto(est.options.default_shots == 5000 and error < 0.015,
              f"`est` usa 5000 disparos y su error es {error:.4f}: las opciones se cambian en `estimator.options`.",
              f"`est` usa {est.options.default_shots} disparos (error {error:.4f}). Debe usar 5000.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: dos perfiles de ejecución

    Completa `crear_estimator(perfil)`:

    - `"crudo"`: sin ninguna corrección, para ver el hardware tal cual: `resilience_level = 0`,
      sin desacoplamiento dinámico y sin twirling.
    - `"protegido"`: desacoplamiento dinámico con la secuencia `"XY4"` y twirling de puertas
      **y** de mediciones.

    Debajo se mide $\\langle ZZ\\rangle$ de un estado de Bell con cada perfil. Idealmente vale 1.
    """)
    return


@app.cell
def _(Estimator, backend):
    def crear_estimator(perfil):
        estimator = Estimator(mode=backend)
        estimator.options.default_shots = 4000
        if perfil == "crudo":
            pass   # ✏️ sin mitigación ni supresión
        else:
            pass   # ✏️ desacoplamiento XY4 y twirling de puertas y de mediciones
        return estimator
    return (crear_estimator,)


@app.cell(hide_code=True)
def _(crear_estimator, veredicto):
    _c = crear_estimator("crudo").options
    _p = crear_estimator("protegido").options
    _crudo = _c.resilience_level == 0 and not _c.dynamical_decoupling.enable and not _c.twirling.enable_gates and not _c.twirling.enable_measure
    _protegido = (_p.dynamical_decoupling.enable and _p.dynamical_decoupling.sequence_type == "XY4"
                  and bool(_p.twirling.enable_gates) and bool(_p.twirling.enable_measure))
    veredicto(_crudo and _protegido,
              "Los dos perfiles están bien configurados.",
              f"Perfil crudo: {'bien' if _crudo else 'revísalo'} · perfil protegido: {'bien' if _protegido else 'revísalo'}.")
    return


@app.cell(hide_code=True)
def _(crear_estimator, mo, medir_zz):
    _filas = []
    for _perfil in ("crudo", "protegido"):
        _v, _e = medir_zz(crear_estimator(_perfil))
        _filas.append(f"| `{_perfil}` | {_v:.3f} | {_e:.4f} |")
    mo.md("| perfil | ⟨ZZ⟩ | error |\n| --- | --- | --- |\n" + "\n".join(_filas))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** una opción que no fijas puede quedar en `None` o traer un valor por defecto.
    ¿Por qué crees que conviene que `Estimator` copie las opciones al crearse en vez de leerlas
    del diccionario original cada vez?
    """)
    return


if __name__ == "__main__":
    app.run()
