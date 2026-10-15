import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.8 · OpenQASM y QPY")


@app.cell(hide_code=True)
def _():
    import io
    import marimo as mo
    from qiskit import QuantumCircuit, qasm2, qpy
    from qiskit.circuit import Parameter

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.8 · OpenQASM y guardar circuitos: práctica

    Tres misiones: leer un programa OpenQASM 2, releer uno antiguo con puertas que ya no
    trae `qelib1.inc` y guardar un circuito completo con QPY.
    """)
    return Parameter, QuantumCircuit, io, mo, qasm2, qpy, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: importar un programa

    Este programa OpenQASM 2 crea un estado de Bell y lo mide. Antes de ejecutar, escribe en
    `prediccion` cuántas instrucciones tendrá el `QuantumCircuit` importado
    (cuenta `h`, `cx` y cada `measure`).
    """)
    return


@app.cell
def _(qasm2):
    programa = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0], q[1];
    measure q -> c;
    """
    importado = qasm2.loads(programa)

    prediccion = None   # ✏️ tu apuesta: ¿cuántas instrucciones?

    print(importado.count_ops())
    importado.draw("text")
    return importado, prediccion


@app.cell(hide_code=True)
def _(importado, prediccion, veredicto):
    veredicto(prediccion == len(importado.data),
              f"Acertaste: {len(importado.data)}. `measure q -> c` se importa como una medición por qubit.",
              f"Tu apuesta ({prediccion}) no coincide con {len(importado.data)}. Una `measure` sobre un registro de 2 bits son dos instrucciones.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: releer un archivo antiguo

    Este programa usa la puerta `rxx` sin definirla: el exportador antiguo de Qiskit suponía
    que `qelib1.inc` la traía. Con las opciones por defecto la importación falla.
    Pasa a `qasm2.loads` el argumento que reconoce esas puertas históricas.
    """)
    return


@app.cell
def _(qasm2):
    programa_antiguo = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    rxx(0.5) q[0], q[1];
    """
    try:
        antiguo = qasm2.loads(programa_antiguo)   # ✏️ añade el argumento que falta
    except qasm2.QASM2ParseError as error:
        antiguo = None
        print("Error al importar:", str(error).splitlines()[0])
    antiguo
    return (antiguo,)


@app.cell(hide_code=True)
def _(antiguo, veredicto):
    veredicto(antiguo is not None and antiguo.count_ops() == {"rxx": 1},
              "Importado: el circuito tiene una puerta `rxx`.",
              "Todavía no se importa. Busca `LEGACY_CUSTOM_INSTRUCTIONS` en `qiskit.qasm2`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: guardar y cargar con QPY

    Escribe `guardar(circuito)`, que devuelva los **bytes** de un archivo QPY, y `cargar(datos)`,
    que reconstruya el circuito. Usa `io.BytesIO()` en lugar de un archivo real; recuerda que
    `qpy.load` siempre devuelve una **lista**.

    El circuito de prueba tiene un `Parameter` libre y un `if_test`. OpenQASM 2 no puede
    representarlo; QPY lo guarda exacto.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, io, qpy):
    theta = Parameter("θ")
    prueba = QuantumCircuit(1, 1)
    prueba.rx(theta, 0)
    prueba.measure(0, 0)
    with prueba.if_test((prueba.clbits[0], 1)):
        prueba.x(0)

    def guardar(circuito):
        # ✏️ escribe el circuito con qpy.dump en un io.BytesIO y devuelve sus bytes (getvalue)
        return b""

    def cargar(datos):
        # ✏️ lee con qpy.load desde io.BytesIO(datos) y devuelve el circuito, no la lista
        return None
    return cargar, guardar, prueba


@app.cell(hide_code=True)
def _(cargar, guardar, prueba, qasm2, veredicto):
    _datos = guardar(prueba)
    _vuelta = cargar(_datos) if _datos else None
    try:
        qasm2.dumps(prueba)
        _qasm2_sirve = True
    except Exception:
        _qasm2_sirve = False
    veredicto(isinstance(_datos, bytes) and _vuelta == prueba and not _qasm2_sirve,
              "QPY devuelve exactamente el mismo circuito, con parámetro y control de flujo; `qasm2.dumps` lo rechaza.",
              "`cargar(guardar(prueba))` debe ser igual a `prueba`. `guardar` devuelve bytes y `cargar` un solo circuito.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿cuándo preferirías OpenQASM y cuándo QPY? Piensa en quién va a leer
    el archivo: otra herramienta, un colega o tú mismo mañana.
    """)
    return


if __name__ == "__main__":
    app.run()
