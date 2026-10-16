import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.1 · Cuenta, planes y credenciales")


@app.cell(hide_code=True)
def _():
    import json
    import tempfile
    from pathlib import Path

    import marimo as mo
    from qiskit_ibm_runtime import QiskitRuntimeService

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Las misiones guardan sus credenciales de práctica en un archivo temporal: ~/.qiskit no se toca.
    archivo = Path(tempfile.mkdtemp()) / "qiskit-ibm.json"
    CLAVE_FALSA = "k" * 44

    mo.md("""

    Tres misiones que **no necesitan cuenta ni red**. Las credenciales de práctica se guardan
    en un archivo temporal con una clave falsa de 44 caracteres; tu `~/.qiskit` no se toca.
    Busca el ✅ en cada misión.
    """)
    return CLAVE_FALSA, Path, QiskitRuntimeService, archivo, json, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: guardar credenciales

    `save_account` escribe un archivo JSON. Antes de ejecutar la celda, predice: ¿el archivo
    guardará la clave **cifrada** o **tal cual**? Ejecuta y mira.
    """)
    return


@app.cell
def _(CLAVE_FALSA, QiskitRuntimeService, archivo):
    QiskitRuntimeService.save_account(
        token=CLAVE_FALSA,
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/practica:curso::",
        name="personal",
        set_as_default=True,
        overwrite=True,
        filename=str(archivo),
    )
    guardadas = QiskitRuntimeService.saved_accounts(filename=str(archivo))
    print(archivo.read_text())
    return (guardadas,)


@app.cell(hide_code=True)
def _(CLAVE_FALSA, guardadas, veredicto):
    veredicto("personal" in guardadas and guardadas["personal"]["token"] == CLAVE_FALSA,
              "La cuenta `personal` está guardada, y la clave está en **texto plano**: por eso nunca va a Git ni a un equipo público.",
              "No aparece la cuenta `personal` con su clave. ¿Cambiaste algo de `save_account`?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuál es la cuenta por defecto

    Guardamos una segunda cuenta, `clase`, pero `QiskitRuntimeService()` sin argumentos carga
    la **predeterminada**. Cambia **un argumento** para que sea `clase` la predeterminada y
    `personal` deje de serlo.
    """)
    return


@app.cell
def _(CLAVE_FALSA, QiskitRuntimeService, archivo, json):
    QiskitRuntimeService.save_account(
        token=CLAVE_FALSA,
        name="clase",
        set_as_default=False,  # ✏️ cambia este argumento
        overwrite=True,
        filename=str(archivo),
    )
    predeterminadas = [n for n, c in json.loads(archivo.read_text()).items() if c.get("is_default_account")]
    predeterminadas
    return (predeterminadas,)


@app.cell(hide_code=True)
def _(predeterminadas, veredicto):
    veredicto(predeterminadas == ["clase"],
              "Solo `clase` es la predeterminada: guardar con `set_as_default=True` quita la marca a la anterior.",
              f"Hoy las predeterminadas son {predeterminadas}. Debe quedar solo `clase`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: ¿cuántos minutos me quedan?

    El plan Open da **10 minutos** de QPU por cada ventana móvil de **28 días**. Escribe
    `minutos_libres(usos, hoy, tope=10)`:

    - `usos` es una lista de `(día, minutos)` con el día en que corriste cada trabajo.
    - Un uso cuenta mientras hayan pasado **menos de 28 días** desde ese día (`0 ≤ hoy − día < 28`).
    - Devuelve el tope menos lo consumido en la ventana.

    La función te sirve antes de cada ejecución real del proyecto Ising.
    """)
    return


@app.cell
def _():
    def minutos_libres(usos, hoy, tope=10):
        consumido = 0   # ✏️ suma los minutos de los usos dentro de la ventana de 28 días
        return tope - consumido
    return (minutos_libres,)


@app.cell(hide_code=True)
def _(minutos_libres, veredicto):
    _usos = [(0, 3), (10, 2), (30, 1)]
    _casos = [(5, 7), (27, 5), (28, 8), (31, 7), (38, 9), (60, 10)]
    _bien = [(hoy, esperado) for hoy, esperado in _casos if abs(minutos_libres(_usos, hoy) - esperado) < 1e-9]
    veredicto(len(_bien) == len(_casos),
              "Tu función respeta la ventana móvil: los usos de hace 28 días o más ya no cuentan.",
              f"Acierta {len(_bien)} de {len(_casos)} casos. Revisa los bordes: el día 27 todavía cuenta el uso del día 0, el 28 no.")
    return


@app.cell(hide_code=True)
def _(mo):
    usar_cuenta = mo.ui.switch(label="Mostrar mi cuenta real (opcional · consulta de red)")
    mo.vstack([
        mo.md("""
        ---
        ### Opcional: tu cuenta real

        Si ya guardaste una cuenta con `save_account`, este interruptor muestra su instancia.
        Apagado, o sin cuenta guardada, la celda no hace nada.
        """),
        usar_cuenta,
    ])
    return (usar_cuenta,)


@app.cell(hide_code=True)
def _(QiskitRuntimeService, mo, usar_cuenta):
    mo.stop(not usar_cuenta.value, mo.md("_Apagado: este cuaderno no necesita cuenta._"))
    mo.stop(not QiskitRuntimeService.saved_accounts(),
            mo.md("_No hay credenciales guardadas en `~/.qiskit`: nada que mostrar._"))
    from qiskit.exceptions import QiskitError

    try:
        _instancia = QiskitRuntimeService().active_instance()
    except (QiskitError, OSError) as _e:
        mo.stop(True, mo.md(f"No se pudo consultar la cuenta ({type(_e).__name__}): no se muestra nada."))
    mo.md(f"Instancia activa: `{_instancia}`")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el proyecto Ising gasta hasta 1 minuto en cada ejecución real. Con 10
    minutos por ventana de 28 días, ¿cuántas ejecuciones caben antes de que la primera
    vuelva a liberar su tiempo?
    """)
    return


if __name__ == "__main__":
    app.run()
