import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.5 · Colas, tiempos y costos")


@app.cell(hide_code=True)
def _():
    import math
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit.primitives.containers.sampler_pub import SamplerPub
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeFez()

    mo.md("""
    # 7.5 · Colas, tiempos y costos: práctica

    Tres misiones para estimar el uso de QPU antes de enviar nada. Usan `FakeFez`, así que
    no consumen minutos reales. Busca el ✅ en cada una.

    $$\\text{uso} \\approx 2\\,\\text{s} + (\\text{rep\\_delay} + \\text{circuito}) \\times N_{\\text{ejecuciones}}$$
    """)
    return (
        Parameter,
        QuantumCircuit,
        SamplerPub,
        backend,
        generate_preset_pass_manager,
        math,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: estimar un estado de Bell

    Un estado de Bell con 4096 disparos en Fez. **Antes de ejecutar, predice** cuántos
    segundos de QPU usará. La celda suma la duración del circuito programado, la del `reset`
    y el `rep_delay`, y lo multiplica por las ejecuciones.
    """)
    return


@app.cell
def _(QuantumCircuit, backend, generate_preset_pass_manager, math):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()

    pm = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
    por_ejecucion = pm.run(bell).estimate_duration(backend.target, unit="s")
    por_ejecucion += backend.target["reset"][(0,)].duration + backend.default_rep_delay

    uso_bell = math.ceil(2 + por_ejecucion * 4096)
    print(f"cada ejecución: {por_ejecucion * 1e6:.0f} µs · uso estimado: {uso_bell} s")
    return (uso_bell,)


@app.cell(hide_code=True)
def _(uso_bell, veredicto):
    veredicto(uso_bell == 4,
              "Unos 3 s (2 s de sobrecarga + 4096 ejecuciones de ~0,25 ms), que se redondean a 4 s.",
              "Debería salir 4 s. ¿Cambiaste los disparos o el circuito?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: contar ejecuciones de un PUB

    Un PUB con un circuito de un parámetro y **4 valores** (una matriz de forma `(4, 1)`),
    con 2000 disparos, genera 4 circuitos. Corrige `ejecuciones` para que cuente
    circuitos × disparos. Pista: `pub.shape` es la forma del lote de circuitos.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, SamplerPub, np):
    angulo = Parameter("θ")
    barrido = QuantumCircuit(1)
    barrido.rx(angulo, 0)
    barrido.measure_all()

    shots = 2000
    pub = SamplerPub.coerce((barrido, np.linspace(0, np.pi, 4).reshape(4, 1)), shots=shots)
    ejecuciones = shots   # ✏️ multiplica por el número de circuitos del PUB
    print("forma del PUB:", pub.shape, "· ejecuciones:", ejecuciones)
    return (ejecuciones,)


@app.cell(hide_code=True)
def _(ejecuciones, veredicto):
    veredicto(ejecuciones == 8000,
              "8000 ejecuciones: el *broadcasting* genera 4 circuitos y cada uno se dispara 2000 veces.",
              f"Cuentas {ejecuciones}. Son circuitos × disparos, no solo disparos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: `estimar_uso`

    Convierte la cuenta de la misión 🟢 en una función `estimar_uso(backend, qc, ejecuciones)`
    que devuelva los segundos de QPU, redondeados hacia arriba:

    1. programa `qc` con `optimization_level=0` y `scheduling_method="alap"`;
    2. suma la duración del `reset` (`backend.target["reset"][(0,)]`) y `backend.default_rep_delay`;
    3. aplica la fórmula con 2 s de sobrecarga.
    """)
    return


@app.cell
def _(generate_preset_pass_manager, math):
    def estimar_uso(backend, qc, ejecuciones):
        return 0   # ✏️ 2 s + (rep_delay + reset + circuito) × ejecuciones, hacia arriba
    return (estimar_uso,)


@app.cell(hide_code=True)
def _(QuantumCircuit, backend, estimar_uso, veredicto):
    def _ghz(n):
        qc = QuantumCircuit(n)
        qc.h(0)
        for k in range(n - 1):
            qc.cx(k, k + 1)
        qc.measure_all()
        return qc

    _bell = _ghz(2)
    _bell_4096 = estimar_uso(backend, _bell, 4096)
    _g5 = estimar_uso(backend, _ghz(5), 100_000)
    _g5_doble = estimar_uso(backend, _ghz(5), 200_000)
    # El tiempo variable crece linealmente con las ejecuciones. Los 2 s de sobrecarga no.
    _lineal = abs((_g5_doble - 2) - 2 * (_g5 - 2)) <= 2
    veredicto(_bell_4096 == 4 and _g5 > _bell_4096 and _lineal,
              f"Bell con 4096 disparos: {_bell_4096} s. GHZ de 5 qubits con 100 000: {_g5} s.",
              f"Bell con 4096 disparos debería dar 4 s (da {_bell_4096}); con GHZ-5 y 100 000 disparos da {_g5} s, "
              f"y con el doble {_g5_doble} s: el tiempo variable debe duplicarse.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** la mitigación añade circuitos (por ejemplo, el aprendizaje de ruido de PEA
    o PEC). ¿Cómo cambia la estimación? Antes de cada ejecución real de tu proyecto, ¿qué
    número calcularías y con qué lo compararías?
    """)
    return


if __name__ == "__main__":
    app.run()
