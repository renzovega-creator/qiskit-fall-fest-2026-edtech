import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="10.4 · Soporte, comunidad y citas")


@app.cell(hide_code=True)
def _():
    from datetime import date
    from importlib.metadata import version

    import marimo as mo
    from qiskit_ibm_runtime.fake_provider import FakeFez, FakeSherbrooke

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 10.4 · Soporte, comunidad y citas: práctica

    Citar bien es parte de participar en la comunidad. En tres misiones construyes las citas
    de un artículo: el software con su versión, cada QPU por su nombre y la sección completa.
    Usas backends simulados (`FakeFez`, `FakeSherbrooke`), así que no necesitas cuenta.
    """)
    return FakeFez, FakeSherbrooke, date, mo, version, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: citar un programa de IBM Quantum

    La guía de preguntas frecuentes da este formato para un programa:
    *IBM Quantum (año). Nombre (Version x.y.z) [computer software]. https://quantum.cloud.ibm.com/*.
    Ejecuta la celda: toma la versión instalada, no una que escribas a mano.
    """)
    return


@app.cell
def _(date, version):
    def cita_programa(nombre, paquete):
        return f"IBM Quantum ({date.today().year}). {nombre} (Version {version(paquete)}) [computer software]. https://quantum.cloud.ibm.com/"

    cita_runtime = cita_programa("Qiskit IBM Runtime", "qiskit-ibm-runtime")
    print(cita_runtime)
    return cita_runtime, cita_programa


@app.cell(hide_code=True)
def _(cita_runtime, date, veredicto, version):
    veredicto(f"Version {version('qiskit-ibm-runtime')})" in cita_runtime and f"({date.today().year})" in cita_runtime,
              "La cita lleva el año actual y la versión instalada de `qiskit-ibm-runtime`.",
              "La cita debe llevar el año actual y la versión que tienes instalada.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: citar un QPU por su nombre y versión

    Los QPU se citan por su nombre único, con la versión, y conviene nombrar el procesador.
    `cita_qpu` solo sirve para `ibm_fez`, porque tiene el nombre, la versión y la familia escritos
    a mano. Hazla servir para cualquier backend con `backend.name`, `backend.backend_version`
    y `backend.processor_type["family"]`.
    """)
    return


@app.cell
def _(FakeFez):
    def cita_qpu(backend):
        # ✏️ usa los datos de `backend` en lugar de escribirlos a mano
        return "In this paper we used `ibm_fez` (v1.2.8), an IBM Quantum Heron processor."

    cita_qpu(FakeFez())
    return (cita_qpu,)


@app.cell(hide_code=True)
def _(FakeFez, FakeSherbrooke, cita_qpu, veredicto):
    _fez, _sher = FakeFez(), FakeSherbrooke()
    veredicto(cita_qpu(_fez) == f"In this paper we used `{_fez.name}` (v{_fez.backend_version}), an IBM Quantum Heron processor."
              and cita_qpu(_sher) == f"In this paper we used `{_sher.name}` (v{_sher.backend_version}), an IBM Quantum Eagle processor.",
              "Funciona con cualquier backend: nombre, versión y familia salen del propio objeto.",
              f"Con `{_sher.name}` devuelve: {cita_qpu(_sher)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la sección de citas de un artículo

    Escribe `seccion_de_citas(backends, anio)`. Devuelve un texto con tres partes, una por línea:
    el agradecimiento (`AGRADECIMIENTO`), una frase por cada backend (usa tu `cita_qpu`) y la
    referencia `IBM Quantum. https://quantum.cloud.ibm.com/, <año>`.
    """)
    return


@app.cell
def _(cita_qpu):
    AGRADECIMIENTO = ("We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
                      "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team.")

    def seccion_de_citas(backends, anio):
        # ✏️ agradecimiento, una frase por backend y la referencia
        return ""

    print(seccion_de_citas([], 2026))
    return AGRADECIMIENTO, seccion_de_citas


@app.cell(hide_code=True)
def _(AGRADECIMIENTO, FakeFez, FakeSherbrooke, cita_qpu, seccion_de_citas, veredicto):
    _bs = [FakeFez(), FakeSherbrooke()]
    veredicto(seccion_de_citas(_bs, 2026).split("\n") == [AGRADECIMIENTO, cita_qpu(_bs[0]), cita_qpu(_bs[1]),
                                                           "IBM Quantum. https://quantum.cloud.ibm.com/, 2026"],
              "La sección tiene el agradecimiento, una frase por QPU y la referencia con el año.",
              "Debe devolver cuatro líneas: agradecimiento, una frase por backend (en orden) y la referencia con el año.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en el hito X tu informe final lleva esta sección. ¿Qué más necesita un
    lector para reproducir tus resultados: versiones, semillas, el nombre del QPU y la fecha
    de la ejecución?
    """)
    return


if __name__ == "__main__":
    app.run()
