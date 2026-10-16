import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.4 · Los procesadores de IBM")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeFez()

    mo.md("""
    # 7.4 · Los procesadores de IBM: práctica

    Tres misiones con `FakeFez`, una copia local de las propiedades de `ibm_fez`: no
    necesitas cuenta. Busca el ✅ en cada una.
    """)
    return backend, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: leer las propiedades

    Ejecuta la celda: nombre, tamaño, familia, el $T_1$ del qubit 1 y lo que dura medir
    frente a una `cz`. **Antes de ejecutar, predice** cuántas veces más dura una medición.
    """)
    return


@app.cell
def _(backend):
    medir = backend.target["measure"][(0,)].duration
    cz = backend.target["cz"][(0, 1)].duration

    print(backend.name, backend.num_qubits, backend.processor_type)
    print(f"T1 del qubit 1: {backend.qubit_properties(1).t1 * 1e6:.0f} µs")
    print(f"medir dura {medir * 1e6:.2f} µs; una CZ, {cz * 1e9:.0f} ns")
    print(f"medir dura {medir / cz:.1f} veces más")
    return cz, medir


@app.cell(hide_code=True)
def _(backend, cz, medir, veredicto):
    veredicto(backend.num_qubits == 156 and backend.processor_type["family"] == "Heron" and medir > 10 * cz,
              f"Fez es un Heron de 156 qubits y medir dura {medir / cz:.0f} veces lo que una `cz`.",
              "Deberían salir 156 qubits, familia Heron, y una medición mucho más larga que la `cz`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: el qubit que más tarda en decaer

    Un $T_1$ largo da más tiempo para trabajar. Cambia `mejor_t1` para que sea el índice del
    qubit de Fez con **mayor** $T_1$. Pista: `backend.qubit_properties(q).t1`.
    """)
    return


@app.cell
def _(backend):
    mejor_t1 = 0   # ✏️ índice del qubit con mayor T1
    print(f"qubit {mejor_t1}: T1 = {backend.qubit_properties(mejor_t1).t1 * 1e6:.0f} µs")
    return (mejor_t1,)


@app.cell(hide_code=True)
def _(backend, mejor_t1, veredicto):
    _todos = [backend.qubit_properties(q).t1 for q in range(backend.num_qubits)]
    veredicto(backend.qubit_properties(mejor_t1).t1 == max(_todos),
              f"El qubit {mejor_t1} tiene el mayor $T_1$ de Fez: {max(_todos) * 1e6:.0f} µs.",
              "Hay otro qubit con $T_1$ mayor. Recórrelos todos con `max(range(backend.num_qubits), key=…)`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la mejor cadena de qubits

    Una cadena de espines de $k$ sitios necesita $k$ qubits seguidos, cada uno acoplado al
    siguiente. Escribe `mejor_cadena(backend, k)`: la lista de $k$ qubits distintos, acoplados
    por `cz` uno tras otro, con el **menor error total** de `cz`.

    Pista: `backend.target["cz"]` tiene una entrada `(a, b)` por cada par acoplado, y su
    `.error`. Con $k$ pequeño basta recorrer todos los caminos.
    """)
    return


@app.cell
def _():
    def mejor_cadena(backend, k):
        cz = backend.target["cz"]
        return list(range(k))   # ✏️ busca la cadena de menor error
    return (mejor_cadena,)


@app.cell(hide_code=True)
def _(backend, mejor_cadena, veredicto):
    _cz = backend.target["cz"]
    _vecinos = {}
    for (_a, _b), _p in _cz.items():
        _vecinos.setdefault(_a, {})[_b] = _p.error

    def _optimo(k):
        mejor = [float("inf")]

        def avanzar(ruta, error):
            if len(ruta) == k:
                mejor[0] = min(mejor[0], error)
                return
            for sig, e in _vecinos[ruta[-1]].items():
                if sig not in ruta:
                    avanzar(ruta + [sig], error + e)
        for inicio in _vecinos:
            avanzar([inicio], 0.0)
        return mejor[0]

    def _error(cadena):
        return sum(_cz[(a, b)].error for a, b in zip(cadena, cadena[1:]))

    _fallos = []
    for _k in (3, 4, 5):
        _c = mejor_cadena(backend, _k)
        if len(_c) != _k or len(set(_c)) != _k or any((a, b) not in _cz for a, b in zip(_c, _c[1:])):
            _fallos.append(f"k={_k}: {_c} no es una cadena acoplada de {_k} qubits distintos")
        elif _error(_c) > _optimo(_k) + 1e-12:
            _fallos.append(f"k={_k}: error {_error(_c):.4f}, el mínimo es {_optimo(_k):.4f}")
    veredicto(not _fallos,
              f"Cadenas óptimas para k = 3, 4 y 5. Con k = 5: {mejor_cadena(backend, 5)}, error total {_error(mejor_cadena(backend, 5)):.4f}.",
              "; ".join(_fallos))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** estas propiedades son una foto de un día. Si calibran de nuevo, ¿la
    mejor cadena sigue siendo la misma? ¿Cuándo conviene elegirla, y cuándo dejar que el
    transpilador lo decida?
    """)
    return


if __name__ == "__main__":
    app.run()
