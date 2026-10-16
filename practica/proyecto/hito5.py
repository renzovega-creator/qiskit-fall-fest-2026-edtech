import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito V")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.exceptions import QiskitError
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Parámetros del proyecto: los mismos que usarás para comparar con hardware.
    N, J, h, dt, K = 4, 1.0, 1.0, 0.25, 6
    DISPAROS = 4096
    PRESUPUESTO_S = 60

    mo.md(f"""
    # Proyecto Ising · Hito V: primera ejecución en un QPU real

    Este hito cierra el proyecto: la **magnetización** $M(t)=\\frac1N\\sum_i\\langle Z_i\\rangle$ de una
    cadena de ${N}$ espines que parte de $|0000\\rangle$, con $J={J:g}$, $h={h:g}$, pasos de
    $dt={dt:g}$ y de 1 a {K} pasos de Trotter. **Presupuesto: como máximo {PRESUPUESTO_S} s de QPU.**

    El cuaderno corre completo en un procesador **falso** (`FakeManilaV2`, 5 qubits) y no
    necesita cuenta. El interruptor de abajo envía el trabajo a un QPU real con tu cuenta
    guardada.
    """)
    return (
        DISPAROS,
        Estimator,
        J,
        K,
        N,
        PRESUPUESTO_S,
        QiskitError,
        QiskitRuntimeService,
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        FakeManilaV2,
        dt,
        expm,
        generate_preset_pass_manager,
        h,
        mo,
        np,
        plt,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    real = mo.ui.switch(label="⚠️ QPU REAL: enviar el trabajo con mi cuenta guardada (consume minutos del plan)")
    enviar = mo.ui.run_button(label="Enviar al QPU real")
    mo.vstack([
        mo.md("## ⚠️ Interruptor del QPU real\nApagado por defecto. Aunque lo enciendas, nada se envía hasta que pulses el botón."),
        real,
        enviar,
    ])
    return enviar, real


@app.cell(hide_code=True)
def _(FakeManilaV2, QiskitError, QiskitRuntimeService, N, mo, real):
    es_real = False
    backend = FakeManilaV2()
    aviso = "Procesador **falso** `FakeManilaV2`: no consume minutos."
    if real.value:
        if QiskitRuntimeService.saved_accounts():
            try:
                backend = QiskitRuntimeService().least_busy(operational=True, simulator=False, min_num_qubits=N)
                es_real = True
                aviso = f"QPU **real** `{backend.name}`. Revisa la estimación antes de enviar."
            except (QiskitError, OSError) as _e:
                aviso = f"No se pudo elegir un QPU real ({type(_e).__name__}): se usa el procesador falso."
        else:
            aviso = "No hay ninguna cuenta guardada (lección 5.1): se usa el procesador falso."
    mo.callout(mo.md(aviso), kind="warn" if es_real else "neutral")
    return backend, es_real


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: recalcula lo de los hitos anteriores

    Reunimos lo que ya hiciste: el Hamiltoniano de Ising de $N$ espines (hito I), los pasos de
    Trotter encadenados (hito II), la evolución exacta con `expm` y la magnetización
    (hitos III y IV). La curva exacta y la de Trotter ideal son tu **referencia**: el QPU no
    puede mejorarlas.
    """)
    return


@app.cell
def _(J, K, N, QuantumCircuit, SparsePauliOp, Statevector, dt, expm, h, np):
    def ising(n, J, h):
        zz = [("I" * (n - i - 2) + "ZZ" + "I" * i, J) for i in range(n - 1)]
        x = [("I" * (n - i - 1) + "X" + "I" * i, h) for i in range(n)]
        return SparsePauliOp.from_list(zz + x)

    def trotter(n, J, h, dt, k):
        qc = QuantumCircuit(n)
        for _ in range(k):
            for i in range(n - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(n):
                qc.rx(2 * h * dt, i)
        return qc

    magnetizacion = SparsePauliOp.from_list([("I" * (N - i - 1) + "Z" + "I" * i, 1 / N) for i in range(N)])

    _U = expm(-1j * ising(N, J, h).to_matrix() * dt)
    _psi = np.zeros(2**N, dtype=complex)
    _psi[0] = 1
    exacto = []
    for _ in range(K):
        _psi = _U @ _psi
        exacto.append(float(np.real(np.vdot(_psi, magnetizacion.to_matrix() @ _psi))))

    circuitos = [trotter(N, J, h, dt, k) for k in range(1, K + 1)]
    ideal = [float(Statevector.from_instruction(c).expectation_value(magnetizacion).real) for c in circuitos]
    print("exacto:", np.round(exacto, 3))
    print("Trotter ideal:", np.round(ideal, 3))
    return circuitos, exacto, ideal, magnetizacion


@app.cell(hide_code=True)
def _(K, exacto, ideal, np, veredicto):
    veredicto(len(exacto) == K and abs(exacto[0] - 0.884) < 2e-3 and np.max(np.abs(np.array(exacto) - ideal)) < 0.03,
              "La referencia está lista: Trotter ideal sigue a la curva exacta con un error máximo de "
              f"{np.max(np.abs(np.array(exacto) - ideal)):.3f}.",
              "Algo falla en la referencia: $M$ tras el primer paso debería ser ≈ 0,884.")
    return


@app.cell(hide_code=True)
def _(backend, circuitos, generate_preset_pass_manager, magnetizacion, mo):
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isas = [pm.run(c) for c in circuitos]
    observables = [magnetizacion.apply_layout(c.layout) for c in isas]
    mo.md("**Circuitos transpilados** (`" + backend.name + "`): "
          + ", ".join(f"{k} paso{'s' if k > 1 else ''}: profundidad {c.depth()}, {c.num_nonlocal_gates()} CX/CZ"
                      for k, c in enumerate(isas, start=1)))
    return isas, observables


@app.cell(hide_code=True)
def _(DISPAROS, backend, generate_preset_pass_manager, isas):
    # La guarda de presupuesto y la comprobación de 🟡 usan esta estimación, no la de `estimar_uso`.
    _pm = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
    _espera = backend.target["reset"][(0,)].duration + backend.default_rep_delay
    uso_ref = 2.0 + sum((_pm.run(i).estimate_duration(backend.target, unit="s") + _espera) * DISPAROS for i in isas)
    return (uso_ref,)


@app.cell(hide_code=True)
def _(DISPAROS, PRESUPUESTO_S, mo):
    mo.md(f"""
    ## 🟡 Modifica: estima el uso de QPU antes de enviar

    La regla de la lección 7.5:

    $$\\text{{uso}} \\approx 2\\,\\text{{s}} + (\\text{{rep\\_delay}} + \\text{{duración del circuito}}) \\times N_{{\\text{{ejecuciones}}}}$$

    Aquí hay {DISPAROS} disparos por circuito y un circuito por cada número de pasos. La
    función `estimar_uso` calcula la duración programada de cada circuito y la espera entre
    ejecuciones (`reset` más `rep_delay`), pero se le olvida sumar esa espera. Corrígela y
    comprueba si cabe en los {PRESUPUESTO_S} s.
    """)
    return


@app.cell
def _(DISPAROS, backend, generate_preset_pass_manager, isas):
    def estimar_uso(isas, backend, disparos):
        pm_t = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
        espera = backend.target["reset"][(0,)].duration + backend.default_rep_delay
        uso = 2.0
        for isa in isas:
            duracion = pm_t.run(isa).estimate_duration(backend.target, unit="s")
            uso += duracion * disparos   # ✏️ falta la espera entre ejecuciones
        return uso

    uso_s = estimar_uso(isas, backend, DISPAROS)
    print(f"Uso estimado: {uso_s:.1f} s")
    return estimar_uso, uso_s


@app.cell(hide_code=True)
def _(PRESUPUESTO_S, uso_ref, uso_s, veredicto):
    veredicto(abs(uso_s - uso_ref) < 0.01 * uso_ref,
              f"Estimación: {uso_s:.1f} s, un {uso_s / PRESUPUESTO_S:.0%} del presupuesto de {PRESUPUESTO_S} s. "
              + ("Cabe." if uso_s <= PRESUPUESTO_S else "No cabe: baja los disparos o los pasos."),
              f"La estimación ({uso_s:.1f} s) no cuadra con {uso_ref:.1f} s. Cada ejecución dura el circuito más la espera (`reset` y `rep_delay`).")
    return


@app.cell(hide_code=True)
def _(DISPAROS, PRESUPUESTO_S, mo):
    mo.md(f"""
    ## 🔴 Crea: ejecuta con `Estimator`

    Escribe `ejecutar(isas, observables, backend, disparos)`. Debe:

    1. Crear un `Estimator(mode=backend)` **sin mitigación** (`resilience_level = 0`): queremos
       ver el ruido tal cual, con `default_shots = disparos` y
       `max_execution_time = {PRESUPUESTO_S}` como tope de seguridad.
    2. Enviar un PUB `(circuito, observable)` por cada paso y devolver la lista de valores
       esperados como números `float`.

    3. Si `backend` es un `FakeManilaV2`, fija `options.simulator.seed_simulator = 5` para que
       el resultado sea reproducible. En hardware real esa opción no existe.

    Con {DISPAROS} disparos y sin mitigación, el ruido baja la curva unos centésimos respecto
    al ideal.
    """)
    return


@app.cell
def _(Estimator, FakeManilaV2, PRESUPUESTO_S):
    def ejecutar(isas, observables, backend, disparos):
        return [0.0] * len(isas)   # ✏️ opciones, un PUB por circuito, lista de float
    return (ejecutar,)


@app.cell
def _(DISPAROS, PRESUPUESTO_S, backend, ejecutar, enviar, es_real, isas, mo, observables, uso_ref):
    mo.stop(es_real and uso_ref > PRESUPUESTO_S,
            mo.callout(mo.md(f"Estimación {uso_ref:.1f} s > {PRESUPUESTO_S} s: no se envía. Baja los disparos o los pasos."), kind="danger"))
    mo.stop(es_real and not enviar.value,
            mo.md("Pulsa **Enviar al QPU real** cuando hayas revisado la estimación."))
    medido = ejecutar(isas, observables, backend, DISPAROS)
    print("medido:", [round(m, 3) for m in medido])
    return (medido,)


@app.cell(hide_code=True)
def _(es_real, ideal, medido, np, veredicto):
    _tol = 0.25 if es_real else 0.12
    _rms = float(np.sqrt(np.mean((np.array(medido) - np.array(ideal)) ** 2))) if len(medido) == len(ideal) else float("inf")
    veredicto(_rms < _tol and all(isinstance(m, float) for m in medido) and any(abs(m) > 0.05 for m in medido),
              f"El ruido te separa del ideal por {_rms:.3f} (RMS). La curva medida es la que presentarás.",
              f"El RMS contra la curva ideal es {_rms:.3f}; debe ser menor que {_tol}. Revisa las opciones y que devuelvas un `float` por circuito.")
    return


@app.cell(hide_code=True)
def _(K, exacto, ideal, medido, plt):
    _pasos = list(range(1, K + 1))
    _fig, _ax = plt.subplots(figsize=(6, 3))
    _ax.plot(_pasos, exacto, "k-", label="exacto")
    _ax.plot(_pasos, ideal, "o--", label="Trotter ideal")
    _ax.plot(_pasos, medido, "s-", label="medido")
    _ax.set_xlabel("pasos de Trotter")
    _ax.set_ylabel("magnetización M")
    _ax.legend()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué curva te separa más de la exacta, el error de Trotter o el ruido del
    procesador? ¿Cómo cambia eso al añadir pasos?
    """)
    return


if __name__ == "__main__":
    app.run()
