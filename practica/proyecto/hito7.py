import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito VII")


@app.cell(hide_code=True)
def _():
    import math
    import marimo as mo
    import numpy as np
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import Batch
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2, FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito VII: puertas fraccionales y modo batch

    La cadena de espines

    $$H = J \\sum_{i} Z_i Z_{i+1} \\; + \\; h \\sum_i X_i$$

    se evoluciona con pasos de Trotter hechos de `rzz` y `rx`, justo las dos puertas que los
    QPU de IBM ofrecen como **fraccionales**. Hoy lo compruebas, mides varios tiempos en un
    **lote** y preparas la **segunda ejecución real**, que consume minutos de tu plan Open.

    Todo corre en local con backends simulados. Solo se toca un QPU si activas el interruptor
    de más abajo.
    """)
    return (
        Batch,
        Estimator,
        FakeBelemV2,
        FakeFez,
        GenericBackendV2,
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        expm,
        generate_preset_pass_manager,
        math,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    J = mo.ui.slider(0.1, 2.0, step=0.1, value=1.0, label="J (acoplamiento ZZ)", show_value=True)
    h = mo.ui.slider(0.0, 2.0, step=0.1, value=0.5, label="h (campo transversal)", show_value=True)
    dt = mo.ui.slider(0.01, 0.5, step=0.01, value=0.1, label="dt (paso de tiempo)", show_value=True)
    espines = mo.ui.slider(3, 5, step=1, value=4, label="espines", show_value=True)
    mo.vstack([mo.md("## Parámetros\nMuévelos cuando termines las misiones y mira qué cambia."),
               J, h, dt, espines])
    return J, dt, espines, h


@app.cell(hide_code=True)
def _(mo):
    gastado = mo.ui.number(0, 600, step=10, value=60,
                           label="segundos de QPU ya usados en este periodo de 28 días")
    real = mo.ui.switch(label="Ejecutar en un QPU real")
    enviar = mo.ui.run_button(label="Enviar el lote")
    mo.vstack([
        mo.md("""
        ## 🔌 Presupuesto y interruptor

        El plan Open da **600 s** de QPU cada 28 días. Apunta aquí lo que llevas gastado (la
        primera ejecución real del hito V) y deja el interruptor **apagado** hasta tener las
        tres misiones en ✅. Con el interruptor encendido, el envío ocurre solo al pulsar el
        botón: mover un deslizador nunca gasta minutos.
        """),
        gastado,
        real,
        enviar,
    ])
    return enviar, gastado, real


@app.cell(hide_code=True)
def _(J, QuantumCircuit, SparsePauliOp, Statevector, dt, espines, expm, h, np):
    # Recalcula aquí los resultados de los hitos anteriores.
    n = espines.value
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J.value) for i in range(n - 1)] + [("X", [i], h.value) for i in range(n)],
        num_qubits=n,
    )
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)

    def cadena(pasos):
        qc = QuantumCircuit(n)
        for _ in range(pasos):
            for _q in range(1, n - 1, 2):
                qc.rzz(2 * J.value * dt.value, _q, _q + 1)
            for _q in range(0, n - 1, 2):
                qc.rzz(2 * J.value * dt.value, _q, _q + 1)
            for _q in range(n):
                qc.rx(2 * h.value * dt.value, _q)
        return qc

    def magnetizacion_exacta(t):
        _psi0 = np.zeros(2**n)
        _psi0[0] = 1
        _psi = expm(-1j * H.to_matrix() * t) @ _psi0
        return float(np.vdot(_psi, M.to_matrix() @ _psi).real)

    def magnetizacion_trotter(pasos):
        return float(Statevector(cadena(pasos)).expectation_value(M).real)

    return H, M, cadena, magnetizacion_exacta, magnetizacion_trotter, n


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: la cadena con y sin fraccionales

    Transpila la cadena de 6 pasos para un backend con `cz` y otro que añade `rx` y `rzz`.
    **Antes de ejecutar, predice** cuántas `cz` necesita el convencional.
    """)
    return


@app.cell
def _(GenericBackendV2, cadena, generate_preset_pass_manager, n):
    filas = {}
    for _nombre, _base in (("convencional", ["cz", "rz", "sx", "x"]),
                           ("fraccional", ["cz", "rz", "sx", "x", "rx", "rzz"])):
        _backend = GenericBackendV2(n, basis_gates=_base, seed=1)
        _isa = generate_preset_pass_manager(3, backend=_backend, scheduling_method="alap").run(cadena(6))
        _ops = _isa.count_ops()
        filas[_nombre] = (_ops.get("cz", 0), _ops.get("rzz", 0),
                          round(_isa.estimate_duration(_backend.target, unit="s") * 1e6, 2))
    filas
    return (filas,)


@app.cell(hide_code=True)
def _(filas, n, veredicto):
    _conv, _frac = filas["convencional"], filas["fraccional"]
    veredicto(_conv[0] == 12 * (n - 1) and _frac[0] == 0 and _frac[1] == 6 * (n - 1),
              f"{_conv[0]} `cz` frente a {_frac[1]} `rzz`; el circuito dura {_conv[2]} µs frente a {_frac[2]} µs.",
              f"Con {n} espines y 6 pasos deberían salir {12 * (n - 1)} `cz` y {6 * (n - 1)} `rzz`, y ninguna `cz` en el fraccional.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: medir los tiempos en un lote

    Medimos la magnetización en los pasos 1 a 4. Un `Batch` envía un trabajo por paso y los
    ejecuta sin esperar entre ellos. En modo local (`FakeBelemV2`) el lote no cambia el
    resultado, pero la sintaxis es la que usarías con un QPU. Ahora solo mide el paso 1:
    cambia `pasos_medidos` para medir **los pasos 1, 2, 3 y 4**.
    """)
    return


@app.cell
def _(
    Batch,
    Estimator,
    FakeBelemV2,
    M,
    cadena,
    generate_preset_pass_manager,
):
    pasos_medidos = [1]   # ✏️ los pasos 1, 2, 3 y 4

    _backend = FakeBelemV2()
    _pm = generate_preset_pass_manager(backend=_backend, optimization_level=1)
    with Batch(backend=_backend) as lote:
        _estimador = Estimator(mode=lote)
        _trabajos = []
        for _p in pasos_medidos:
            _isa = _pm.run(cadena(_p))
            _trabajos.append(_estimador.run([(_isa, M.apply_layout(_isa.layout))], precision=0.02))
        medidas = [float(_t.result()[0].data.evs) for _t in _trabajos]
    print("pasos medidos:", pasos_medidos)
    print("magnetización:", [round(_m, 3) for _m in medidas])
    return medidas, pasos_medidos


@app.cell(hide_code=True)
def _(magnetizacion_trotter, medidas, pasos_medidos, veredicto):
    _ideal = [magnetizacion_trotter(_p) for _p in pasos_medidos]
    veredicto(list(pasos_medidos) == [1, 2, 3, 4]
              and all(abs(_m - _i) < 0.15 for _m, _i in zip(medidas, _ideal)),
              "Cuatro trabajos en un lote, todos a menos de 0,15 del valor sin ruido: el ruido de "
              "`FakeBelemV2` baja la magnetización un poco más con cada paso.",
              "Mide los pasos 1, 2, 3 y 4, en ese orden. Las medidas deben estar a menos de 0,15 del valor sin ruido.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la guardia de la segunda ejecución real

    Antes de gastar minutos reales hay que estimar el uso con la fórmula de la lección 7.5:

    $$\\text{uso} \\approx 2\\,\\text{s} + (\\text{rep\\_delay} + \\text{reset} + \\text{circuito}) \\times N_{\\text{ejecuciones}}$$

    Escribe `guardia(backend, circuitos, disparos, restante_s, activado)`, que devuelva la
    tupla `(permitido, uso_s)`:

    - `uso_s`: la suma de los usos de **cada circuito** con `disparos` ejecuciones, cada uno
      con sus 2 s de sobrecarga, redondeada hacia arriba (cada circuito programado con
      `optimization_level=0` y `scheduling_method="alap"`, ya transpilado para el backend);
    - `permitido`: `True` solo si el interruptor está `activado` **y** `uso_s <= restante_s`.
    """)
    return


@app.cell
def _(generate_preset_pass_manager, math):
    def guardia(backend, circuitos, disparos, restante_s, activado):
        uso_s = 0   # ✏️ suma 2 s + (rep_delay + reset + circuito) × disparos de cada circuito
        permitido = False   # ✏️ interruptor activado y uso dentro del presupuesto
        return permitido, uso_s
    return (guardia,)


@app.cell(hide_code=True)
def _(FakeFez, QuantumCircuit, generate_preset_pass_manager, guardia, veredicto):
    _backend = FakeFez()
    _bell = QuantumCircuit(2)
    _bell.h(0)
    _bell.cx(0, 1)
    _bell.measure_all()
    _isa = generate_preset_pass_manager(backend=_backend, optimization_level=1).run(_bell)
    _casos = [
        (([_isa], 4096, 540, True), (True, 4)),
        (([_isa] * 4, 4096, 540, True), (True, 16)),
        (([_isa], 4096, 540, False), (False, 4)),
        (([_isa] * 4, 4096, 10, True), (False, 16)),
        (([_isa], 4096 * 100, 540, True), (True, 106)),
        (([_isa], 4096 * 100, 100, True), (False, 106)),
    ]
    _salidas = [guardia(_backend, *args) for args, _ in _casos]
    _esperadas = [esperado for _, esperado in _casos]
    veredicto(_salidas == _esperadas,
              "La guardia acierta en los 6 casos: respeta el interruptor y el presupuesto restante.",
              f"Salidas {_salidas}, esperadas {_esperadas}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ▶️ La segunda ejecución real

    Con las tres misiones en ✅, esta celda estima el uso de los cuatro pasos de arriba sobre
    `FakeFez` con puertas convencionales (una cota superior: las fraccionales duran menos), y
    **solo si el interruptor está activado y cabe en tu presupuesto** envía el lote al QPU
    menos ocupado que ofrece puertas fraccionales. Con el interruptor apagado no toca la red.
    """)
    return


@app.cell
def _(
    Batch,
    Estimator,
    FakeFez,
    M,
    cadena,
    enviar,
    gastado,
    generate_preset_pass_manager,
    guardia,
    mo,
    real,
):
    _fez = FakeFez()
    _pm = generate_preset_pass_manager(backend=_fez, optimization_level=1)
    _isas = [_pm.run(cadena(_p)) for _p in (1, 2, 3, 4)]
    _permitido, _uso = guardia(_fez, _isas, 4096, 600 - gastado.value, real.value)
    _lineas = [f"Uso estimado: **{_uso} s** de {600 - gastado.value} s restantes."]
    if _permitido and enviar.value:
        from qiskit_ibm_runtime import QiskitRuntimeService
        _servicio = QiskitRuntimeService()
        _qpu = _servicio.least_busy(
            operational=True, simulator=False, use_fractional_gates=True,
            filters=lambda _b: "rzz" in _b.target.operation_names,
        )
        _pm_real = generate_preset_pass_manager(backend=_qpu, optimization_level=1)
        with Batch(backend=_qpu, max_time=f"{max(_uso, 60)}s") as _lote:
            _estimador = Estimator(mode=_lote)
            _trabajos = []
            for _p in (1, 2, 3, 4):
                _isa = _pm_real.run(cadena(_p))
                _trabajos.append(_estimador.run([(_isa, M.apply_layout(_isa.layout))], precision=0.02))
        _lineas.append(f"Enviado a **{_qpu.name}**: {[_t.job_id() for _t in _trabajos]}")
    else:
        _lineas.append("No se envió nada: falta el interruptor o el botón, o el uso supera el presupuesto.")
    mo.md("\n\n".join(_lineas))
    return


@app.cell(hide_code=True)
def _(dt, magnetizacion_exacta, magnetizacion_trotter, mo):
    mo.md(f"""
    ---
    **Para pensar:** con estos parámetros, al paso 4 la magnetización exacta vale
    {magnetizacion_exacta(4 * dt.value):.4f} y la de Trotter {magnetizacion_trotter(4):.4f}. ¿Qué error
    de hardware esperas ver en el QPU real, comparado con esa diferencia? Decidirlo antes de
    ejecutar es parte del método.
    """)
    return


if __name__ == "__main__":
    app.run()
