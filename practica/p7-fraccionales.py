import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.2 · Puertas fraccionales")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def compilar(circuito):
        """Transpila para un backend sin y con puertas fraccionales; devuelve (CZ, RZZ, µs) de cada uno."""
        n = circuito.num_qubits
        filas = {}
        for nombre, base in (("convencional", ["cz", "rz", "sx", "x"]),
                             ("fraccional", ["cz", "rz", "sx", "x", "rx", "rzz"])):
            backend = GenericBackendV2(n, basis_gates=base, seed=1)
            isa = generate_preset_pass_manager(3, backend=backend, scheduling_method="alap").run(circuito)
            ops = isa.count_ops()
            filas[nombre] = (ops.get("cz", 0), ops.get("rzz", 0),
                             round(isa.estimate_duration(backend.target, unit="s") * 1e6, 2))
        return filas

    def tabla(filas):
        return mo.md("| backend | CZ | RZZ | duración |\n| --- | --: | --: | --: |\n" +
                     "\n".join(f"| {k} | {cz} | {rzz} | {us} µs |" for k, (cz, rzz, us) in filas.items()))

    mo.md("""
    # 7.2 · Puertas fraccionales: práctica

    Tres misiones con la cadena de Ising de la lección. Se transpila para dos backends
    genéricos, uno sin y otro con `rx` y `rzz` nativas, así que no necesitas cuenta. Busca
    el ✅ en cada una.
    """)
    return QuantumCircuit, compilar, mo, np, tabla, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: cuánto acortan las fraccionales

    Cinco qubits, tres pasos: capas de `rx` y dos capas de `rzz` por paso. Antes de
    ejecutar, predice cuántas `cz` necesita el backend convencional (cada `rzz` se
    descompone en dos).
    """)
    return


@app.cell
def _(QuantumCircuit, compilar):
    n, pasos = 5, 3
    ising = QuantumCircuit(n)
    for _ in range(pasos):
        for _q in range(n):
            ising.rx(0.1, _q)
        for _q in range(1, n - 1, 2):
            ising.rzz(0.1, _q, _q + 1)
        for _q in range(0, n - 1, 2):
            ising.rzz(0.1, _q, _q + 1)
        ising.barrier()

    filas = compilar(ising)
    filas
    return (filas,)


@app.cell(hide_code=True)
def _(filas, mo, tabla, veredicto):
    _conv, _frac = filas["convencional"], filas["fraccional"]
    mo.vstack([
        tabla(filas),
        veredicto(_conv[0] == 24 and _frac[0] == 0 and _frac[1] == 12 and _frac[2] < _conv[2],
                  f"{_conv[0]} `cz` frente a {_frac[1]} `rzz`: el circuito dura {_conv[2] / _frac[2]:.1f} veces menos.",
                  "Deberían salir 24 `cz` en el convencional y 12 `rzz` (sin `cz`) en el fraccional."),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuándo ayudan menos

    Con ángulos $R_{ZZ}$ arbitrarios el convencional necesita dos `cz` por `rzz`. Cambia
    `theta_zz` por un ángulo con el que **necesite menos de 24**. Pista: hay ángulos para los
    que la descomposición se acorta, múltiplos de $\\pi/2$. Mira qué pasa con la duración.
    """)
    return


@app.cell
def _(QuantumCircuit, compilar, np):
    theta_zz = 0.1   # ✏️ prueba otro ángulo

    cadena = QuantumCircuit(5)
    for _ in range(3):
        for _q in range(5):
            cadena.rx(0.1, _q)
        for _q in range(1, 4, 2):
            cadena.rzz(theta_zz, _q, _q + 1)
        for _q in range(0, 4, 2):
            cadena.rzz(theta_zz, _q, _q + 1)
        cadena.barrier()

    filas_theta = compilar(cadena)
    filas_theta
    return (filas_theta,)


@app.cell(hide_code=True)
def _(filas_theta, mo, tabla, veredicto):
    _conv, _frac = filas_theta["convencional"], filas_theta["fraccional"]
    mo.vstack([
        tabla(filas_theta),
        veredicto(_conv[0] < 24,
                  f"El convencional baja a {_conv[0]} `cz`. Con las fraccionales siguen siendo {_frac[1]} `rzz`: "
                  f"lo que más cambia es la duración ({_conv[2]} µs frente a {_frac[2]} µs).",
                  "Todavía salen 24 `cz`. Prueba un múltiplo de $\\pi/2$ (`np.pi / 2`)."),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la cadena de Ising con parámetros

    Escribe `cadena_ising(n, pasos, theta_x, theta_zz)`: en cada paso, una capa de `rx` en
    todos los qubits, una capa de `rzz` entre los pares $(1,2), (3,4), \\dots$ y otra entre
    los pares $(0,1), (2,3), \\dots$, y una `barrier()`.

    La comprobación transpila tu circuito para varios tamaños y cuenta las puertas.
    """)
    return


@app.cell
def _(QuantumCircuit):
    def cadena_ising(n, pasos, theta_x, theta_zz):
        qc = QuantumCircuit(n)
        # ✏️ tu código aquí
        return qc
    return (cadena_ising,)


@app.cell(hide_code=True)
def _(cadena_ising, compilar, veredicto):
    _fallos = []
    for _n, _pasos in ((4, 2), (5, 3), (6, 3)):
        _f = compilar(cadena_ising(_n, _pasos, 0.1, 0.1))
        _esperado = ((2 * _pasos * (_n - 1), 0), (0, _pasos * (_n - 1)))
        _obtenido = (_f["convencional"][:2], _f["fraccional"][:2])
        if _obtenido != _esperado:
            _fallos.append(f"n={_n}, pasos={_pasos}: (CZ, RZZ) = {_obtenido}, esperado {_esperado}")
    veredicto(not _fallos,
              "Tu cadena necesita $2\\cdot\\text{pasos}\\cdot(n-1)$ `cz` en el convencional y "
              "$\\text{pasos}\\cdot(n-1)$ `rzz` en el fraccional.",
              "El conteo de puertas no coincide: " + "; ".join(_fallos))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en el proyecto Ising cada paso de tiempo usa `rx` y `rzz`. ¿Cuántos
    pasos de más podrías añadir en el mismo tiempo de circuito si usaras fraccionales?
    """)
    return


if __name__ == "__main__":
    app.run()
