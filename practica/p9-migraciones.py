import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="9.5 · Versiones y migraciones")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.circuit import ClassicalRegister, QuantumRegister
    from qiskit_ibm_runtime.options_models import EstimatorOptions

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 9.5 · Versiones y migraciones: práctica

    Tres migraciones reales, de menor a mayor: de `c_if` a `if_test` (Qiskit 2.0), de las
    opciones como `dataclass` a modelos de Pydantic (primitivas del lado del cliente) y la
    regla de «un trabajo por valor de precisión». Todo se ejecuta en local.
    """)
    return (
        ClassicalRegister,
        EstimatorOptions,
        QuantumCircuit,
        QuantumRegister,
        mo,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: de `c_if` a `if_test`

    En Qiskit 2.0 desapareció `c_if`. La condición ahora es un bloque: dentro de
    `with qc.if_test((registro, valor)):` van las puertas que solo se aplican si el registro
    clásico vale `valor`. El circuito de abajo aplica una X al qubit 0 si se midió `11`.
    """)
    return


@app.cell
def _(ClassicalRegister, QuantumCircuit, QuantumRegister):
    qr, cr = QuantumRegister(2, "q"), ClassicalRegister(2, "c")
    qc = QuantumCircuit(qr, cr)
    qc.h([0, 1])
    qc.measure(qr, cr)
    with qc.if_test((cr, 3)):
        qc.x(0)
    ops = dict(qc.count_ops())
    ops
    return (ops,)


@app.cell(hide_code=True)
def _(QuantumCircuit, ops, veredicto):
    veredicto(ops == {"h": 2, "measure": 2, "if_else": 1} and not hasattr(QuantumCircuit(1).x(0), "c_if"),
              "La condición es una sola instrucción `if_else`, y las puertas ya no tienen `c_if`.",
              f"Salió {ops}. Debería haber `h`, `measure` e `if_else`, una vez cada tipo.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: las opciones del Estimator del lado del cliente

    Las clases de opciones de `qiskit_ibm_runtime.options_models` son modelos de Pydantic.
    Ya no se pueden convertir con `dataclasses.asdict(opciones)`. Cambia la línea para que
    use el método de Pydantic que lo reemplaza.
    """)
    return


@app.cell
def _(EstimatorOptions):
    opciones = EstimatorOptions()
    opciones.default_shots = 2000
    opciones_dict = None   # ✏️ usa el método de Pydantic
    return opciones, opciones_dict


@app.cell(hide_code=True)
def _(opciones, opciones_dict, veredicto):
    try:
        opciones.seed_estimator = 7
        _quitada = "se aceptó"
    except Exception as e:
        _quitada = type(e).__name__
    veredicto(isinstance(opciones_dict, dict) and opciones_dict.get("default_shots") == 2000,
              f"Las opciones son un diccionario con `default_shots = 2000`. Y `seed_estimator`, que ya no existe, da `{_quitada}`.",
              "`opciones_dict` debería ser un diccionario con `default_shots` igual a 2000.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un trabajo por precisión

    El Estimator del lado del cliente no admite precisiones distintas en un mismo trabajo.
    Escribe `dividir(pubs)`: recibe una lista de pares `(nombre, precisión)` y devuelve la
    lista de grupos de nombres, **uno por valor de precisión**, en el orden en que aparece
    cada valor. Para `[("A", 0.01), ("B", 0.05), ("C", 0.01)]` debe dar
    `[["A", "C"], ["B"]]`: dos trabajos, no tres.
    """)
    return


@app.cell
def _():
    def dividir(pubs):
        # ✏️ tu código aquí
        return [[nombre] for nombre, _ in pubs]
    return (dividir,)


@app.cell(hide_code=True)
def _(dividir, veredicto):
    try:
        _a = dividir([("A", 0.01), ("B", 0.05), ("C", 0.01)])
        _b = dividir([("P", 0.1), ("Q", 0.1), ("R", 0.5), ("S", 0.2), ("T", 0.5)])
        _ok = _a == [["A", "C"], ["B"]] and _b == [["P", "Q"], ["R", "T"], ["S"]]
        _no = f"Salió {_a} y {_b}. Agrupa por valor de precisión, no por PUB."
    except Exception as e:
        _ok, _no = False, f"`dividir` falla con {type(e).__name__}."
    veredicto(_ok,
              "Dos trabajos para A, B y C: `[A, C]` a 0,01 y `[B]` a 0,05. Cada trabajo tiene un costo fijo, por eso se agrupa.",
              _no)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué parte de estas migraciones puede hacer una herramienta que
    reescribe el código (`flake8-qiskit-migration`, una *skill* de IA) y cuál exige que
    entiendas qué cambió de comportamiento?
    """)
    return


if __name__ == "__main__":
    app.run()
