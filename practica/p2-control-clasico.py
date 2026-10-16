import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.7 · Control clásico")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer.primitives import SamplerV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def conteos(circuito, shots=512):
        return SamplerV2(seed=11).run([circuito], shots=shots).result()[0].data.c.get_counts()

    mo.md("""
    # 2.7 · Control clásico y feedforward: práctica

    Una misión con un circuito dinámico, simulado con el Sampler de Qiskit Aer: un
    `if_test`.
    """)
    return ClassicalRegister, QuantumCircuit, QuantumRegister, conteos, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: corregir el azar

    El circuito lanza una moneda con H, la mide y, **si salió 1**, aplica una X; luego mide otra
    vez. Antes de ejecutar, escribe en `prediccion` el resultado final: `"0"`, `"1"` o `"azar"`.
    """)
    return


@app.cell
def _(ClassicalRegister, QuantumCircuit, QuantumRegister, conteos):
    q = QuantumRegister(1, "q")
    c = ClassicalRegister(1, "c")
    moneda = QuantumCircuit(q, c)
    moneda.h(q[0])
    moneda.measure(q[0], c[0])
    with moneda.if_test((c[0], 1)):
        moneda.x(q[0])
    moneda.measure(q[0], c[0])

    prediccion = ""   # ✏️ tu apuesta: "0", "1" o "azar"

    resultado = conteos(moneda)
    resultado
    return prediccion, resultado


@app.cell(hide_code=True)
def _(prediccion, resultado, veredicto):
    _real = next(iter(resultado)) if len(resultado) == 1 else "azar"
    veredicto(prediccion == _real,
              f"Acertaste: `{_real}`. Cuando salía 1, la X lo devolvía a 0; cuando salía 0, no se tocaba.",
              f"Tu apuesta {prediccion!r} no coincide con {dict(resultado)}. Sigue las dos ramas de la moneda.")
    return


if __name__ == "__main__":
    app.run()
