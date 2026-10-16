import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="9.2 · La API de C de Qiskit")


@app.cell(hide_code=True)
def _():
    import re
    from pathlib import Path

    import marimo as mo
    import qiskit
    import qiskit.capi
    from packaging.requirements import Requirement
    from qiskit.quantum_info import SparsePauliOp

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 9.2 · La API de C de Qiskit: práctica

    Compilar un programa en C necesita la biblioteca independiente (`make c` en el código
    de Qiskit). Aquí no la compilas: trabajas con lo que sí trae tu entorno, las cabeceras
    de C que vienen con el paquete `qiskit`, y reproduces en Python lo que hace el
    programa de la lección.
    """)
    return Path, Requirement, SparsePauliOp, mo, qiskit, re, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el observable del programa en C

    El programa de la lección crea un observable de 100 qubits con **un** término,
    $2\\,X_0 Y_1 Z_2$, y escribe `num_qubits: 100` y `num_terms: 1`. Esta es su versión en
    Python: un coeficiente, los operadores de Pauli y los índices de los qubits.
    """)
    return


@app.cell
def _(SparsePauliOp):
    obs = SparsePauliOp.from_sparse_list([("XYZ", [0, 1, 2], 2)], num_qubits=100)
    num_qubits, num_terms = obs.num_qubits, len(obs)
    print(f"num_qubits: {num_qubits}\nnum_terms: {num_terms}")
    return num_qubits, num_terms


@app.cell(hide_code=True)
def _(num_qubits, num_terms, veredicto):
    veredicto((num_qubits, num_terms) == (100, 1),
              "Salen `100` y `1`, igual que el programa en C: tres operadores de Pauli son un solo término.",
              f"Salen {num_qubits} y {num_terms}; el programa en C imprime 100 y 1.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un segundo término

    En C añadirías una segunda llamada a `qk_obs_add_term`. En Python, agrega a la lista el
    término $0{,}5\\,Z_{99}$: la cadena `"Z"`, el qubit `[99]` y el coeficiente `0.5`.
    """)
    return


@app.cell
def _(SparsePauliOp):
    terminos = [("XYZ", [0, 1, 2], 2)]   # ✏️ añade el segundo término
    obs2 = SparsePauliOp.from_sparse_list(terminos, num_qubits=100)
    len(obs2)
    return (obs2,)


@app.cell(hide_code=True)
def _(obs2, veredicto):
    _coef = dict(zip(obs2.paulis.to_labels(), obs2.coeffs)).get("Z" + "I" * 99)
    veredicto(len(obs2) == 2 and _coef is not None and abs(_coef - 0.5) < 1e-12,
              "El observable tiene 2 términos y $0{,}5\\,Z_{99}$ es uno de ellos.",
              f"Tiene {len(obs2)} términos; debería tener 2, con $0{{,}}5\\,Z_{{99}}$.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: fijar la versión menor

    La API de C es experimental: una extensión compilada con Qiskit 2.4.0 funciona con
    2.4.1, pero puede fallar con 2.5.0. Por eso el `pyproject.toml` de la guía fija
    `qiskit~=2.4.0`.

    Escribe `restriccion(version)`: dada la versión con la que compilas, devuelve la
    dependencia que deja pasar solo esa versión menor. Para `"2.4.0"` debe dar
    `"qiskit~=2.4.0"`.
    """)
    return


@app.cell
def _():
    def restriccion(version):
        # ✏️ tu código aquí
        return None
    return (restriccion,)


@app.cell(hide_code=True)
def _(Requirement, restriccion, veredicto):
    try:
        _req = Requirement(restriccion("2.4.0"))
        _casos = {"2.4.0": True, "2.4.1": True, "2.5.0": False, "2.3.9": False}
        _ok = _req.name == "qiskit" and all(_req.specifier.contains(v) == esperado for v, esperado in _casos.items())
        _no = f"`{_req}` no deja pasar exactamente 2.4.x: debería aceptar 2.4.0 y 2.4.1 y rechazar 2.5.0."
    except Exception as e:
        _ok, _no = False, f"Todavía no devuelve una dependencia válida ({type(e).__name__})."
    veredicto(_ok,
              "`qiskit~=2.4.0` acepta 2.4.x y rechaza 2.5.0: la compatibilidad es solo dentro de la misma versión menor.",
              _no)
    return


@app.cell(hide_code=True)
def _(Path, mo, qiskit, re):
    _include = Path(qiskit.capi.get_include())
    _cabecera = re.search(r'#define QISKIT_VERSION "([^"]+)"', (_include / "qiskit" / "version.h").read_text()).group(1)
    mo.md(f"""
    **Tus cabeceras de C** están en `{_include}`: versión `{_cabecera}`, la misma que el
    paquete de Python (`{qiskit.__version__}`).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** las cabeceras de C viajan dentro del paquete `qiskit`, así que siempre
    coinciden con tu instalación. ¿Qué pasaría con una extensión que ya compilaste si
    actualizas Qiskit a la siguiente versión menor sin recompilar?
    """)
    return


if __name__ == "__main__":
    app.run()
