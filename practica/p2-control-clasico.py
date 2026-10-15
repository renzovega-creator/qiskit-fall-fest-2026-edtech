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

    Tres misiones con circuitos dinámicos, simulados con el Sampler de Qiskit Aer: un
    `if_test`, su condición y un `while_loop`.
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


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: que el resultado final sea siempre 1

    Es el mismo circuito, pero ahora quieres terminar **siempre en 1**. Cambia solo la
    condición del `if_test` para que la X se aplique en la rama correcta.
    """)
    return


@app.cell
def _(ClassicalRegister, QuantumCircuit, QuantumRegister, conteos):
    q2 = QuantumRegister(1, "q")
    c2 = ClassicalRegister(1, "c")
    siempre_uno = QuantumCircuit(q2, c2)
    siempre_uno.h(q2[0])
    siempre_uno.measure(q2[0], c2[0])
    with siempre_uno.if_test((c2[0], 1)):   # ✏️ ¿con qué valor del bit hay que aplicar la X?
        siempre_uno.x(q2[0])
    siempre_uno.measure(q2[0], c2[0])

    resultado_uno = conteos(siempre_uno)
    resultado_uno
    return (resultado_uno,)


@app.cell(hide_code=True)
def _(resultado_uno, veredicto):
    veredicto(set(resultado_uno) == {"1"},
              "Siempre `1`: la X solo se aplica cuando la moneda salió 0.",
              f"Salen {dict(resultado_uno)}. Busca que solo aparezca `1`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: repetir hasta tener éxito

    Escribe `hasta_uno()`: un circuito que lanza la moneda (H y medición) y **repite mientras
    el bit valga 0**, con un `while_loop`. Al salir del bucle el bit es siempre 1.
    Mira cómo se hizo el `while_loop` de la lección, con la condición `(clbits, 0b11)`; aquí
    la condición es `(c, 0)`.
    """)
    return


@app.cell
def _(ClassicalRegister, QuantumCircuit, QuantumRegister):
    def hasta_uno():
        q = QuantumRegister(1, "q")
        c = ClassicalRegister(1, "c")
        qc = QuantumCircuit(q, c)
        # ✏️ H y medir una vez; después, while_loop mientras c valga 0: H y medir otra vez
        return qc
    return (hasta_uno,)


@app.cell(hide_code=True)
def _(conteos, hasta_uno, veredicto):
    _qc = hasta_uno()
    _res = conteos(_qc, 500) if _qc.num_clbits == 1 else {}
    _tiene_bucle = any(i.operation.name == "while_loop" for i in _qc.data)
    veredicto(_tiene_bucle and set(_res) == {"1"},
              "Siempre `1`, y sin ninguna X: el bucle repite la moneda hasta que sale 1.",
              "Necesito un `while_loop` que repita la moneda y un resultado final que sea siempre `1`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `hasta_uno()` no tiene un número fijo de puertas: depende del azar.
    ¿Qué implica eso para estimar cuánto tardará en un computador real?
    """)
    return


if __name__ == "__main__":
    app.run()
