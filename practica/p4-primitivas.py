import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.1 · Las primitivas")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.primitives import StatevectorEstimator, StatevectorSampler

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""

    Tres misiones con las dos primitivas y con sus implementaciones. Todo corre en tu
    equipo, sin cuenta. Busca el ✅ en cada una.
    """)
    return QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: Estimator y Sampler sobre el mismo estado

    El estado de Bell, sin mediciones para Estimator y con `measure_all()` para Sampler.
    Antes de ejecutar, predice los tres valores esperados.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)

    observables = [SparsePauliOp(p) for p in ["ZZ", "ZI", "XX"]]
    evs = StatevectorEstimator().run([(bell, observables)]).result()[0].data.evs

    bell_medido = bell.copy()
    bell_medido.measure_all()
    conteos_bell = StatevectorSampler(seed=3).run([bell_medido], shots=1024).result()[0].data.meas.get_counts()
    print("Estimator:", evs.round(3))
    print("Sampler:  ", conteos_bell)
    return bell_medido, conteos_bell, evs


@app.cell(hide_code=True)
def _(conteos_bell, evs, np, veredicto):
    veredicto(np.allclose(evs, [1, 0, 1]) and set(conteos_bell) == {"00", "11"},
              "Estimator da ⟨ZZ⟩ = 1, ⟨ZI⟩ = 0 y ⟨XX⟩ = 1; Sampler solo ve `00` y `11`. Son dos vistas del mismo estado.",
              "Deberían salir [1, 0, 1] y solo `00` y `11`. ¿Cambiaste el circuito?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cambia de implementación, no de código

    `BackendSamplerV2` envuelve cualquier backend en la interfaz de primitivas. Sustituye
    `StatevectorSampler` por `BackendSamplerV2(backend=backend)` y deja el resto igual:
    `run` recibe lo mismo y devuelve lo mismo. El backend falso tiene ruido, así que
    el circuito se transpila antes (la lección 3.1 explica cómo).
    """)
    return


@app.cell
def _(StatevectorSampler, bell_medido):
    from qiskit.primitives import BackendSamplerV2
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    backend = GenericBackendV2(2, seed=1)
    isa_bell = generate_preset_pass_manager(1, backend=backend).run(bell_medido)

    # ✏️ cambia esta línea por BackendSamplerV2(backend=backend)
    sampler = StatevectorSampler(seed=3)

    conteos_backend = sampler.run([isa_bell], shots=1024).result()[0].data.meas.get_counts()
    print(type(sampler).__name__, conteos_backend)
    return BackendSamplerV2, conteos_backend, sampler


@app.cell(hide_code=True)
def _(BackendSamplerV2, conteos_backend, sampler, veredicto):
    _total = sum(conteos_backend.values())
    _buenos = conteos_backend.get("00", 0) + conteos_backend.get("11", 0)
    veredicto(isinstance(sampler, BackendSamplerV2) and _total == 1024 and _buenos > 0.9 * _total,
              f"Mismo `run`, otra implementación: {_buenos} de {_total} disparos en `00` o `11`, y el resto es ruido del backend.",
              "Todavía usas otra primitiva. Crea `sampler` con `BackendSamplerV2(backend=backend)`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el mismo número por dos caminos

    Un circuito con $R_y(0.8)$ en el qubit 0 tiene $\\langle Z_0\\rangle = \\cos 0.8 \\approx 0.697$.
    Estimator lo da directamente. Con Sampler solo tienes cadenas de bits: escribe
    `z_desde_conteos(conteos, k)`, que devuelva $\\langle Z_k\\rangle$ a partir de los conteos.
    Cuidado: en la cadena, el qubit 0 es el carácter de la **derecha**.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler):
    ry = QuantumCircuit(3)
    ry.ry(0.8, 0)

    z0_estimator = float(StatevectorEstimator().run([(ry, SparsePauliOp("IIZ"))]).result()[0].data.evs)

    ry_medido = ry.copy()
    ry_medido.measure_all()
    conteos_ry = StatevectorSampler(seed=5).run([ry_medido], shots=20000).result()[0].data.meas.get_counts()

    def z_desde_conteos(conteos, k):
        # ✏️ promedio de +1 (bit 0) y -1 (bit 1) del qubit k sobre todos los disparos
        return 0.0

    z0_sampler = z_desde_conteos(conteos_ry, 0)
    print(f"Estimator: {z0_estimator:.3f} · Sampler: {z0_sampler:.3f}")
    return conteos_ry, z0_estimator, z0_sampler, z_desde_conteos


@app.cell(hide_code=True)
def _(conteos_ry, np, veredicto, z0_estimator, z0_sampler, z_desde_conteos):
    veredicto(abs(z0_estimator - np.cos(0.8)) < 1e-9 and abs(z0_sampler - z0_estimator) < 0.03
              and abs(z_desde_conteos(conteos_ry, 1) - 1) < 1e-9,
              f"Los dos caminos coinciden ({z0_estimator:.3f} frente a {z0_sampler:.3f}) y el qubit 1, que no se tocó, vale 1.",
              "El valor de Sampler no se acerca a cos(0.8). Revisa el bit que miras y el signo.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** Estimator te dio $\\langle Z_0\\rangle$ sin error de muestreo, y Sampler lo
    obtuvo con 20 000 disparos. ¿Para qué observables es imposible obtener el valor desde los
    conteos de una sola medición?
    """)
    return


if __name__ == "__main__":
    app.run()
