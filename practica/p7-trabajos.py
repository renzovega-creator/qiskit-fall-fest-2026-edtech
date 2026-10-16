import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.6 · Monitorear, etiquetar y guardar trabajos")


@app.cell(hide_code=True)
def _():
    import json
    import tempfile
    from pathlib import Path
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorSampler
    from qiskit_ibm_runtime import RuntimeDecoder, RuntimeEncoder

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()

    class TrabajoLocal:
        """Un trabajo con un resultado real de StatevectorSampler. `update_tags` sobrescribe, como en el servicio."""

        def __init__(self, job_id, semilla, etiquetas):
            self._id = job_id
            self.tags = list(etiquetas)
            self._resultado = StatevectorSampler(seed=semilla).run([bell]).result()

        def job_id(self):
            return self._id

        def result(self):
            return self._resultado

        def update_tags(self, nuevas):
            self.tags = list(dict.fromkeys(nuevas))
            return self.tags

    class ServicioLocal:
        """`jobs(job_tags=…)` devuelve los trabajos que tienen todas las etiquetas, como el servicio."""

        def __init__(self):
            self._trabajos = [TrabajoLocal("job-1", 1, ["a", "b"]),
                              TrabajoLocal("job-2", 2, ["a"]),
                              TrabajoLocal("job-3", 3, ["b"])]

        def job(self, job_id):
            return next(t for t in self._trabajos if t.job_id() == job_id)

        def jobs(self, job_tags=()):
            return [t for t in self._trabajos if set(job_tags) <= set(t.tags)]

    mo.md("""
    # 7.6 · Monitorear, etiquetar y guardar trabajos: práctica

    Tres misiones sobre trabajos. Los resultados vienen de `StatevectorSampler`, y el
    servicio de la misión 🟡 y la 🔴 es una copia local que se comporta como describe la
    lección: `update_tags` sobrescribe y `jobs(job_tags=…)` devuelve los trabajos con **todas**
    las etiquetas. No necesitas cuenta.
    """)
    return (
        Path,
        RuntimeDecoder,
        RuntimeEncoder,
        ServicioLocal,
        StatevectorSampler,
        TrabajoLocal,
        bell,
        json,
        mo,
        tempfile,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: guardar y leer un resultado

    Guarda un resultado en disco con `RuntimeEncoder` y léelo con `RuntimeDecoder`.
    **Antes de ejecutar, predice** qué tipo de objeto vuelve y si conserva los conteos.
    """)
    return


@app.cell
def _(RuntimeDecoder, RuntimeEncoder, StatevectorSampler, bell, json, tempfile):
    resultado = StatevectorSampler(seed=3).run([bell]).result()

    with tempfile.TemporaryDirectory() as _carpeta:
        with open(f"{_carpeta}/result.json", "w") as _f:
            json.dump(resultado, _f, cls=RuntimeEncoder)
        with open(f"{_carpeta}/result.json") as _f:
            leido = json.load(_f, cls=RuntimeDecoder)

    print(type(leido).__name__, leido[0].data.meas.get_counts())
    return leido, resultado


@app.cell(hide_code=True)
def _(leido, resultado, veredicto):
    veredicto(type(leido).__name__ == "PrimitiveResult"
              and leido[0].data.meas.get_counts() == resultado[0].data.meas.get_counts(),
              "Vuelve un `PrimitiveResult` con los mismos conteos.",
              "Debería volver un `PrimitiveResult` con los mismos conteos que el original.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: añadir una etiqueta sin perder las otras

    `job-1` tiene las etiquetas `a` y `b`. `update_tags` **sobrescribe**, así que esta línea
    deja solo `c`. Cámbiala para que el trabajo tenga `a`, `b` y `c`.
    """)
    return


@app.cell
def _(ServicioLocal):
    servicio = ServicioLocal()
    trabajo = servicio.job("job-1")
    trabajo.update_tags(["c"])   # ✏️ conserva las etiquetas anteriores
    print(trabajo.tags)
    return servicio, trabajo


@app.cell(hide_code=True)
def _(servicio, trabajo, veredicto):
    veredicto(sorted(trabajo.tags) == ["a", "b", "c"] and trabajo in servicio.jobs(job_tags=["a", "c"]),
              "`job-1` tiene `a`, `b` y `c`, y aparece al buscar por `a` y `c`.",
              f"Ahora tiene {trabajo.tags}. Pasa a `update_tags` la lista completa, no solo la nueva.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: guardar los trabajos de una etiqueta

    Escribe dos funciones:

    - `guardar_por_etiqueta(servicio, etiquetas, carpeta)`: para cada trabajo de
      `servicio.jobs(job_tags=etiquetas)`, guarda su resultado en `carpeta/<job_id>.json` con
      `RuntimeEncoder` y devuelve la lista de `job_id` guardados.
    - `cargar(carpeta, job_id)`: lee ese archivo con `RuntimeDecoder` y devuelve el resultado.
    """)
    return


@app.cell
def _(Path, RuntimeDecoder, RuntimeEncoder, json):
    def guardar_por_etiqueta(servicio, etiquetas, carpeta):
        guardados = []
        # ✏️ un archivo carpeta/<job_id>.json por cada trabajo con esas etiquetas
        return guardados

    def cargar(carpeta, job_id):
        return None   # ✏️ lee carpeta/<job_id>.json con RuntimeDecoder
    return cargar, guardar_por_etiqueta


@app.cell(hide_code=True)
def _(ServicioLocal, cargar, guardar_por_etiqueta, tempfile, veredicto):
    _servicio = ServicioLocal()
    with tempfile.TemporaryDirectory() as _carpeta:
        _guardados = guardar_por_etiqueta(_servicio, ["a"], _carpeta)
        _cargados = {i: cargar(_carpeta, i) for i in _guardados}
    _esperados = {t.job_id() for t in _servicio.jobs(job_tags=["a"])}
    _iguales = set(_guardados) == _esperados and all(
        type(r).__name__ == "PrimitiveResult"
        and r[0].data.meas.get_counts() == _servicio.job(i).result()[0].data.meas.get_counts()
        for i, r in _cargados.items())
    veredicto(_iguales and len(_esperados) == 2,
              f"Guardaste y recuperaste {sorted(_guardados)}: los conteos coinciden con los originales.",
              f"Se guardaron {sorted(_guardados)} y debían guardarse {sorted(_esperados)}, "
              "y al leerlos cada uno debe ser un `PrimitiveResult` con sus conteos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué etiquetas pondrías a los trabajos de tu proyecto Ising para
    encontrar después «la ejecución con TREX, 8 pasos de Trotter»? ¿Qué más guardarías junto al
    resultado?
    """)
    return


if __name__ == "__main__":
    app.run()
