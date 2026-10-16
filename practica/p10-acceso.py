import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="10.2 · Cuentas, grupos de acceso y usuarios")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 10.2 · Cuentas, grupos de acceso y usuarios: práctica

    Tres misiones sobre permisos: qué deja hacer un rol personalizado, cómo derivar uno de
    solo lectura y cómo evitar que una regla dinámica dé más acceso del que pretendes.
    Trabajas con una copia de la tabla de permisos de la guía, sin cuenta ni red.
    """)
    return mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: qué puede hacer un rol personalizado

    Cada permiso `quantum-computing.*` autoriza llamadas concretas de la API. El rol
    «trabajar con instancias» de la lección incluye siete acciones. Antes de ejecutar,
    **predice**: ¿podrá un usuario con ese rol borrar un trabajo (`DELETE /v1/jobs/{id}`)?
    """)
    return


@app.cell
def _():
    P = "quantum-computing."
    ENDPOINTS = {
        ("GET", "/v1/backends"): P + "device.read",
        ("POST", "/v1/jobs"): P + "job.create",
        ("GET", "/v1/jobs"): P + "job.read",
        ("GET", "/v1/jobs/{id}/results"): P + "job.read",
        ("POST", "/v1/jobs/{id}/cancel"): P + "job.cancel",
        ("DELETE", "/v1/jobs/{id}"): P + "job.delete",
        ("GET", "/v1/instances/usage"): P + "instance-usage.read",
        ("POST", "/v1/sessions"): P + "session.create",
        ("PATCH", "/v1/sessions/{id}"): P + "session.update",
    }

    rol_trabajo = {P + a for a in ("device.read", "job.cancel", "job.create", "job.read",
                                   "program.delete", "program.read", "user.logout")}

    def permitidas(rol):
        return [e for e, permiso in ENDPOINTS.items() if permiso in rol]

    for (metodo, ruta), permiso in ENDPOINTS.items():
        print("✔" if permiso in rol_trabajo else "✘", metodo, ruta, "←", permiso)
    return ENDPOINTS, P, permitidas, rol_trabajo


@app.cell(hide_code=True)
def _(permitidas, rol_trabajo, veredicto):
    _ok = permitidas(rol_trabajo)
    veredicto(("GET", "/v1/jobs") in _ok and ("POST", "/v1/jobs") in _ok and ("DELETE", "/v1/jobs/{id}") not in _ok,
              "Puede listar y ejecutar trabajos, pero no borrarlos: `job.delete` es un permiso aparte.",
              "Revisa `rol_trabajo`: debe poder listar y ejecutar trabajos, y no borrarlos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un rol lector a partir del escritor

    La guía propone dos roles: `MLwriter` con **todas** las acciones y `MLreader` sin las de
    cancelar, borrar ni actualizar. Hoy `lector` es una copia de `escritor`, así que puede
    cancelar y borrar. Cambia la línea marcada para quitar esas acciones sin tocar las demás.
    """)
    return


@app.cell
def _(ENDPOINTS):
    escritor = set(ENDPOINTS.values())
    lector = set(escritor)   # ✏️ quita las acciones que terminan en .cancel, .delete o .update
    sorted(lector)
    return escritor, lector


@app.cell(hide_code=True)
def _(escritor, lector, veredicto):
    _sobran = [a for a in lector if a.rsplit(".", 1)[-1] in ("cancel", "delete", "update")]
    _faltan = [a for a in escritor if a.rsplit(".", 1)[-1] not in ("cancel", "delete", "update") and a not in lector]
    veredicto(not _sobran and not _faltan and len(lector) > 0,
              f"`lector` conserva {len(lector)} acciones y ninguna cancela, borra ni actualiza.",
              f"Sobran {sorted(_sobran)}; faltan {sorted(_faltan)}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: detectar valores que son subcadenas de otros

    Las reglas dinámicas de un proveedor de identidad comparan cadenas: la regla `ml` también
    acepta `mlReader`, y `ml` acepta `chemlab`. Escribe `conflictos(valores)`: devuelve la lista
    ordenada de pares `(corto, largo)` en los que `corto` es subcadena de `largo` y son
    distintos. La comparación distingue mayúsculas, como la del proveedor.
    """)
    return


@app.cell
def _():
    def conflictos(valores):
        # ✏️ pares (corto, largo) con corto dentro de largo
        return []

    conflictos(["ml", "chemlab", "mlReader", "fisica"])
    return (conflictos,)


@app.cell(hide_code=True)
def _(conflictos, veredicto):
    veredicto(conflictos(["ml", "chemlab", "mlReader", "fisica"]) == [("ml", "chemlab"), ("ml", "mlReader")]
              and conflictos(["MLreader", "MLwriter", "ml-lab"]) == []
              and conflictos(["ml", "ml"]) == [],
              "Detecta `ml` dentro de `chemlab` y de `mlReader`, y deja en paz `MLreader` y `MLwriter`.",
              "Debe devolver [('ml', 'chemlab'), ('ml', 'mlReader')] para la primera lista y [] si no hay subcadenas.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿qué permisos darías a un auditor que solo debe ver la analítica de uso?
    Busca en la tabla de `ENDPOINTS` cuáles necesitarías y qué te faltaría añadir.
    """)
    return


if __name__ == "__main__":
    app.run()
