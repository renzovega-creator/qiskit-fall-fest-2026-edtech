import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="10.3 · Seguridad y cumplimiento")


@app.cell(hide_code=True)
def _():
    import re
    from collections import Counter

    import marimo as mo

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 10.3 · Seguridad y cumplimiento: práctica

    Tres misiones sobre la parte de la seguridad que te toca: leer la auditoría, buscar claves
    de API en tu código y decidir qué hacer ante una caída regional. Todo con datos de ejemplo,
    sin cuenta ni red. Las claves del cuaderno son inventadas.
    """)
    return Counter, mo, re, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: de la auditoría a los permisos

    Cada evento de actividad corresponde a una llamada de la API, y cada llamada requiere un
    permiso `quantum-computing.*`. Antes de ejecutar, **predice**: en estos siete eventos,
    ¿cuál es el permiso que más se ejerce y cuántas veces?
    """)
    return


@app.cell
def _(Counter):
    P = "quantum-computing."
    REQUIERE = {
        "POST /v1/jobs": P + "job.create",
        "POST /v1/jobs/{id}/cancel": P + "job.cancel",
        "GET /v1/backends": P + "device.read",
        "GET /v1/instances/usage": P + "instance-usage.read",
    }
    eventos = ["POST /v1/jobs", "GET /v1/backends", "POST /v1/jobs", "POST /v1/jobs/{id}/cancel",
               "GET /v1/instances/usage", "GET /v1/backends", "POST /v1/jobs"]

    usados = Counter(REQUIERE[e] for e in eventos)
    for permiso, veces in usados.most_common():
        print(veces, permiso)
    return (usados,)


@app.cell(hide_code=True)
def _(usados, veredicto):
    veredicto(usados.most_common(1) == [("quantum-computing.job.create", 3)] and sum(usados.values()) == 7,
              "`job.create` se ejerce 3 veces de 7: ejecutar trabajos es lo más frecuente.",
              "Revisa el conteo: deben salir 7 eventos y `job.create` debe ser el más frecuente.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: buscar claves de API en tu código

    Una clave en un repositorio público es tu responsabilidad: hay que revocarla y crear otra.
    Mejor es no subirla nunca. El detector de abajo es una heurística que solo reconoce
    `apikey = "..."` con comillas dobles. Amplía el patrón para que también encuentre
    `api_key`, `token` y las comillas simples, sin marcar `token = os.environ[...]`.
    """)
    return


@app.cell
def _(re):
    archivos = {
        "a.py": 'service = QiskitRuntimeService(token="FAKE_TOKEN_0123456789ABCDEF")\n',
        "b.py": "api_key = 'FAKE_KEY_ABCDEFGHIJKLMNOP'\n",
        "c.py": 'apikey = "FAKE_APIKEY_0123456789AB"\n',
        "d.py": 'token = os.environ["QISKIT_IBM_TOKEN"]\n',
        "e.py": 'api_key = ""\n',
    }
    patron = re.compile(r'apikey\s*=\s*"([^"]{20,})"')   # ✏️ api_key, token y comillas simples

    def con_claves(archivos):
        return sorted(nombre for nombre, texto in archivos.items() if patron.search(texto))

    con_claves(archivos)
    return archivos, con_claves


@app.cell(hide_code=True)
def _(archivos, con_claves, veredicto):
    veredicto(con_claves(archivos) == ["a.py", "b.py", "c.py"],
              "Encuentra las tres claves escritas en el código y no marca la que viene del entorno.",
              f"Encuentra {con_claves(archivos)}; deberían ser a.py, b.py y c.py.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: qué hacer ante una caída regional

    Escribe `ante_desastre(region_caida, plan, necesita_qubits_de_la_region, residencia_de_datos)`.
    La regla de la guía: lo recomendado es crear una instancia en la otra región y reenviar los
    trabajos (`"instancia en eu-de"`); si necesitas qubits de esa región o tienes requisitos de
    residencia de datos, hay que esperar la recuperación (`"esperar"`). Las regiones son
    `us-east` y `eu-de`. El plan Open solo existe en `us-east`, así que no puede cambiar de región.
    """)
    return


@app.cell
def _():
    def ante_desastre(region_caida, plan, necesita_qubits_de_la_region, residencia_de_datos):
        # ✏️ "esperar" o "instancia en <otra región>"
        return ""

    ante_desastre("us-east", "Premium", False, False)
    return (ante_desastre,)


@app.cell(hide_code=True)
def _(ante_desastre, veredicto):
    _casos = [
        (("us-east", "Pay-As-You-Go", False, False), "instancia en eu-de"),
        (("eu-de", "Premium", False, False), "instancia en us-east"),
        (("us-east", "Premium", True, False), "esperar"),
        (("eu-de", "Flex", False, True), "esperar"),
        (("us-east", "Open", False, False), "esperar"),
    ]
    _mal = [args for args, esperado in _casos if ante_desastre(*args) != esperado]
    veredicto(not _mal,
              "Los cinco escenarios dan la decisión de la guía.",
              f"Fallan {len(_mal)} de 5 escenarios, por ejemplo {_mal[0] if _mal else ''}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué parte de tu proyecto Ising dependería de qubits concretos de una región,
    y qué parte podrías reenviar sin cambios a otra región?
    """)
    return


if __name__ == "__main__":
    app.run()
