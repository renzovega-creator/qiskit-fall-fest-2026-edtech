import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito VI")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import SamplerV2 as AerSampler
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito VI: mitigar el ruido

    Hasta aquí simulaste la cadena de Ising, la llevaste a un circuito de Trotter y la
    ejecutaste. En el hardware el resultado sale **sesgado** por el ruido. Hoy mides cuánto, y
    cuánto recuperan dos técnicas de la parte VI:

    - **TREX**: corrige el error de lectura calibrándolo con un circuito vacío.
    - **ZNE**: mide con más ruido a propósito (plegando el circuito) y extrapola a ruido cero.

    La pregunta es la del proyecto: ¿qué tan cerca queda cada una del valor **exacto** de la
    magnetización $M_z=\\tfrac1N\\sum_i\\langle Z_i\\rangle$?
    Por defecto corre sobre un simulador con el ruido de `FakeFez`; no necesitas cuenta.
    """)
    return (
        AerSampler,
        AerSimulator,
        FakeFez,
        QuantumCircuit,
        SparsePauliOp,
        Statevector,
        expm,
        generate_preset_pass_manager,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(QuantumCircuit, SparsePauliOp, Statevector, expm, mo, np):
    N, J, h, dt, PASOS = 3, 1.0, 1.0, 0.25, 2

    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(N - 1)] + [("X", [i], h) for i in range(N)], N
    )
    Mz = SparsePauliOp.from_sparse_list([("Z", [i], 1 / N) for i in range(N)], N)

    def trotter(pasos):
        """Hitos I y II: `pasos` pasos de e^{-iH dt}, primero los ZZ y luego los X."""
        qc = QuantumCircuit(N)
        for _ in range(pasos):
            for i in range(N - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(N):
                qc.rx(2 * h * dt, i)
        return qc

    psi0 = np.zeros(2**N)
    psi0[0] = 1
    psi_t = expm(-1j * H.to_matrix() * dt * PASOS) @ psi0
    exacto = float(np.real(np.vdot(psi_t, Mz.to_matrix() @ psi_t)))
    trotter_ideal = float(Statevector(trotter(PASOS)).expectation_value(Mz).real)

    mo.md(f"""
    ## Lo que ya tienes, recalculado

    {N} espines con $J={J}$, $h={h}$, $dt={dt}$ y {PASOS} pasos de Trotter, desde $|000\\rangle$.

    | Referencia | $M_z$ |
    | --- | --- |
    | Exacta (`expm`, hito I) | {exacto:.4f} |
    | Trotter sin ruido (hito II) | {trotter_ideal:.4f} |

    La mitigación apunta al valor de Trotter sin ruido, no al exacto: lo que queda entre los
    dos es error de Trotter, que ningún método de esta parte toca.
    """)
    return Mz, N, PASOS, exacto, trotter, trotter_ideal


@app.cell(hide_code=True)
def _(mo):
    usar_qpu = mo.ui.switch(label="Ejecutar en un QPU real (gasta tiempo de tu plan Open)", value=False)
    mo.vstack([
        mo.md("""
        ## Dónde ejecutar

        Apagado (por defecto), todo corre en local con el ruido de `FakeFez`. Encendido,
        la tanda de circuitos va a `least_busy` con tu cuenta de IBM Quantum Platform (la del
        hito I) y menos disparos. Son 19 circuitos en un solo trabajo; revisa tu consumo en
        la plataforma. Los veredictos siguen igual, pero el resultado depende del dispositivo.
        """),
        usar_qpu,
    ])
    return (usar_qpu,)


@app.cell(hide_code=True)
def _(AerSampler, AerSimulator, FakeFez, N, generate_preset_pass_manager, usar_qpu):
    if usar_qpu.value:
        from qiskit_ibm_runtime import QiskitRuntimeService
        from qiskit_ibm_runtime import SamplerV2 as RuntimeSampler

        backend = QiskitRuntimeService().least_busy(operational=True, simulator=False, min_num_qubits=N)
        sampler = RuntimeSampler(mode=backend)
        disparos = 4000
        objetivo = backend
    else:
        objetivo = FakeFez()
        backend = AerSimulator.from_backend(objetivo)
        sampler = AerSampler.from_backend(backend, options={"backend_options": {"seed_simulator": 3}})
        disparos = 20000
    pm = generate_preset_pass_manager(optimization_level=1, backend=objetivo, seed_transpiler=1)
    return backend, disparos, pm, sampler


@app.cell(hide_code=True)
def _(N, np):
    def magnetizacion(cuentas, volteo=None):
        """Mz medida a partir de las cuentas; el qubit 0 es el bit de más a la derecha.
        `volteo[i]=1` deshace un X puesto antes de medir el qubit i."""
        total = sum(cuentas.values())
        suma = 0.0
        for bits, n in cuentas.items():
            for i in range(N):
                signo = 1 - 2 * int(bits[N - 1 - i])
                if volteo is not None and volteo[i]:
                    signo = -signo
                suma += n * signo
        return suma / (N * total)

    def plegar(qc, k):
        """U (U† U)^k: mismo circuito ideal, 2k+1 veces más puertas (y más ruido)."""
        out = qc.copy()
        for _ in range(k):
            out.barrier()
            out.compose(qc.inverse(), inplace=True)
            out.barrier()
            out.compose(qc, inplace=True)
        return out

    rng = np.random.default_rng(0)
    volteos = [rng.integers(0, 2, N) for _ in range(8)]
    return magnetizacion, plegar, volteos


@app.cell(hide_code=True)
def _(PASOS, QuantumCircuit, N, disparos, pm, plegar, sampler, trotter, volteos):
    def _con_volteos(qc):
        out = []
        for v in volteos:
            q = qc.copy()
            for i, b in enumerate(v):
                if b:
                    q.x(i)
            out.append(q)
        return out

    def _medir(qc):
        qc = qc.copy()
        qc.measure_all()
        return pm.run(qc)

    _base = trotter(PASOS)
    _tw = disparos // 4
    _pubs = (
        [(_medir(_base), None, disparos)]
        + [(_medir(c), None, _tw) for c in _con_volteos(_base)]
        + [(_medir(c), None, _tw) for c in _con_volteos(QuantumCircuit(N))]
        + [(_medir(plegar(_base, k)), None, disparos) for k in (1, 2)]
    )
    _res = [r.data.meas.get_counts() for r in sampler.run(_pubs).result()]
    c_base = _res[0]
    c_tw = _res[1:9]
    c_cal = _res[9:17]
    c_pleg = [c_base] + _res[17:19]
    return c_base, c_cal, c_pleg, c_tw


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: cuánto sesga el ruido

    `c_base` son las cuentas del circuito de Trotter tal cual, sin mitigar. Antes de ejecutar,
    apuesta: ¿la magnetización medida queda por encima o por debajo de la exacta?
    """)
    return


@app.cell
def _(c_base, exacto, magnetizacion):
    sin_mitigar = magnetizacion(c_base)
    print(f"exacta {exacto:.4f} · sin mitigar {sin_mitigar:.4f} · error {abs(sin_mitigar - exacto):.4f}")
    return (sin_mitigar,)


@app.cell(hide_code=True)
def _(exacto, sin_mitigar, trotter_ideal, veredicto):
    _error = abs(sin_mitigar - exacto)
    veredicto(_error > 0.03,
              f"Error de {_error:.3f}: el ruido sesga hacia {'abajo' if sin_mitigar < trotter_ideal else 'arriba'} "
              f"(Trotter sin ruido es {trotter_ideal:.4f}). Este es el número a batir.",
              f"Error de solo {_error:.3f}; con este dispositivo el ruido casi no se nota. Prueba con más pasos de Trotter.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: TREX a mano

    Las ocho cuentas de `c_tw` son el mismo circuito con un $X$ antes de medir en los qubits
    marcados en `volteos`; `magnetizacion(c, v)` ya deshace ese giro. Su promedio, `m_tw`,
    todavía contiene el error de lectura. `c_cal` repite lo mismo con el **circuito vacío**,
    cuyo valor ideal es 1: lo que se aparte de 1 es sesgo de lectura.

    Completa la corrección: $M_z^{\\text{TREX}}=\\dfrac{\\overline{m_{\\text{tw}}}}{\\overline{m_{\\text{cal}}}}$.
    """)
    return


@app.cell
def _(c_cal, c_tw, exacto, magnetizacion, np, volteos):
    m_tw = [magnetizacion(c, v) for c, v in zip(c_tw, volteos)]
    m_cal = [magnetizacion(c, v) for c, v in zip(c_cal, volteos)]
    trex = np.mean(m_tw)   # ✏️ divide entre el promedio de m_cal
    print(f"calibración {np.mean(m_cal):.4f} · TREX {trex:.4f} · error {abs(trex - exacto):.4f}")
    return m_cal, m_tw, trex


@app.cell(hide_code=True)
def _(exacto, m_cal, m_tw, np, sin_mitigar, trex, veredicto):
    _esperado = np.mean(m_tw) / np.mean(m_cal)
    veredicto(abs(trex - _esperado) < 1e-6,
              f"TREX = {trex:.4f}: error {abs(trex - exacto):.4f} frente a {abs(sin_mitigar - exacto):.4f} sin mitigar. "
              "Corrige la lectura, pero no los CZ.",
              "Divide el promedio de `m_tw` entre el de `m_cal`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la extrapolación de ZNE

    `c_pleg` tiene las cuentas con los factores de ruido 1, 3 y 5 (el circuito plegado 0, 1 y
    2 veces). Sus magnetizaciones bajan con el factor: más puertas, más ruido. Escribe
    `extrapolar(factores, valores)` que ajuste $y=Ae^{-b f}$ (una recta en $\\ln y$) y devuelva
    $A$, el valor a factor 0.
    """)
    return


@app.cell
def _(np):
    def extrapolar(factores, valores):
        # ✏️ recta a ln(valores) con np.polyfit y devuelve exp(ordenada en el origen)
        return valores[0]
    return (extrapolar,)


@app.cell
def _(c_pleg, exacto, extrapolar, magnetizacion):
    factores = [1, 3, 5]
    valores_pleg = [magnetizacion(c) for c in c_pleg]
    zne = extrapolar(factores, valores_pleg)
    print(f"valores {[round(v, 4) for v in valores_pleg]} · ZNE {zne:.4f} · error {abs(zne - exacto):.4f}")
    return factores, valores_pleg, zne


@app.cell(hide_code=True)
def _(exacto, extrapolar, np, sin_mitigar, veredicto, zne):
    _f = np.array([1.0, 3.0, 5.0])
    _ok = abs(extrapolar(_f, 0.9 * np.exp(-0.2 * _f)) - 0.9) < 1e-9
    veredicto(_ok,
              f"ZNE = {zne:.4f}: error {abs(zne - exacto):.4f} frente a {abs(sin_mitigar - exacto):.4f} sin mitigar.",
              "Con datos sintéticos 0.9·e^(−0.2 f) tu función debe devolver 0.9.")
    return


@app.cell(hide_code=True)
def _(exacto, mo, sin_mitigar, trex, trotter_ideal, zne):
    _filas = [("Sin mitigar", sin_mitigar), ("TREX", trex), ("ZNE (exponencial)", zne)]
    mo.md(
        "## Resultado\n\n| Método | $M_z$ | Error vs exacto | Error vs Trotter sin ruido |\n| --- | --- | --- | --- |\n"
        + "\n".join(f"| {n} | {v:.4f} | {abs(v - exacto):.4f} | {abs(v - trotter_ideal):.4f} |" for n, v in _filas)
        + f"\n\nExacto: {exacto:.4f} · Trotter sin ruido: {trotter_ideal:.4f}."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿cuánto del error que queda es ruido y cuánto es Trotter? ¿Qué pasa con
    TREX y ZNE si aumentas los pasos de Trotter? En el hito VII repetirás la ejecución real
    con puertas fraccionales (RZZ).
    """)
    return


if __name__ == "__main__":
    app.run()
