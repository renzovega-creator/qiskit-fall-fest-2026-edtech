import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="10.1 · Organizaciones e instancias")


@app.cell(hide_code=True)
def _():
    import json
    import urllib.parse
    from datetime import date, timedelta

    import marimo as mo

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 10.1 · Organizaciones e instancias: práctica

    Tres misiones sobre lo que decide una instancia: qué dice la API de gestión, cuánto
    tiempo te queda en el plan Open y qué pasa con los trabajos al llegar a un límite.
    Todo corre en local con datos de ejemplo: no necesitas cuenta ni red.
    """)
    return date, json, mo, timedelta, urllib, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: leer una instancia por la API de gestión

    La API Resource Controller identifica la instancia por su CRN **codificado** en la ruta
    (cada `:` pasa a `%3A` y cada `/` a `%2F`). La respuesta trae los campos cuánticos en
    `extensions`. Ejecuta la celda con esta respuesta de ejemplo y lee cada línea.
    """)
    return


@app.cell
def _(json, urllib):
    crn = "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef::"
    url = "https://resource-controller.cloud.ibm.com/v2/resource_instances/" + urllib.parse.quote(crn, safe="")

    respuesta = json.loads("""{
      "name": "laboratorio-ml",
      "extensions": {
        "instance_limit_seconds": 3600,
        "usage_allocation_seconds": 3600,
        "backends": ["ANY"]
      }
    }""")
    ext = respuesta["extensions"]

    def puede_usar(ext, backend, plan_backends=("ibm_fez", "ibm_torino")):
        permitidos = ext["backends"]
        if permitidos == ["ANY"]:
            return backend in plan_backends
        return backend in permitidos

    print(url)
    print("límite:", ext["instance_limit_seconds"], "s · asignación:", ext["usage_allocation_seconds"], "s")
    print("¿ibm_fez?", puede_usar(ext, "ibm_fez"), "· ¿con backends = []?", puede_usar({"backends": []}, "ibm_fez"))
    return puede_usar, url


@app.cell(hide_code=True)
def _(puede_usar, url, veredicto):
    veredicto("%3A" in url and "%2F" in url and ":" not in url.split("resource_instances/")[1]
              and puede_usar({"backends": ["ANY"]}, "ibm_fez") and not puede_usar({"backends": []}, "ibm_fez"),
              "El CRN va codificado en la ruta, `[\"ANY\"]` permite todos los backends del plan y `[]` ninguno.",
              "Revisa la URL (el CRN debe ir codificado) y la regla de `backends`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuánto te queda en el plan Open

    El plan Open da **10 minutos (600 s)** de QPU en una ventana móvil de **28 días**. La
    función `restante` suma *todos* los usos que le pasas, así que cuenta también los de hace
    mucho. Antes de ejecutar, **predice**: con los tres usos de abajo (hace 40, 20 y 3 días),
    ¿cuántos segundos deberían quedarte? Luego corrige la función para que solo cuente la ventana.
    """)
    return


@app.cell
def _(date, timedelta):
    hoy = date(2026, 10, 15)
    usos = [(hoy - timedelta(days=40), 300), (hoy - timedelta(days=20), 250), (hoy - timedelta(days=3), 100)]

    def restante(usos, hoy, tope=600):
        gastado = sum(seg for fecha, seg in usos)   # ✏️ ¿cuentan todos los usos?
        return tope - gastado

    segundos_restantes = restante(usos, hoy)
    segundos_restantes
    return hoy, restante, usos


@app.cell(hide_code=True)
def _(hoy, restante, timedelta, usos, veredicto):
    _viejo = [(hoy - timedelta(days=100), 600)]
    _reciente = [(hoy - timedelta(days=1), 100)]
    veredicto(restante(usos, hoy) == 250 and restante(_viejo, hoy) == 600 and restante(_reciente, hoy) == 500,
              "Te quedan 250 s: el uso de hace 40 días ya salió de la ventana.",
              f"`restante` devuelve {restante(usos, hoy)} s. Un uso de hace 40 días no debería contar.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: qué pasa con los trabajos al llegar al límite

    Escribe `tras_alcanzar(trabajos, es_limite)`. Cada trabajo es `{"id": ..., "estado": "ejecutando" | "pendiente"}`.
    Devuelve una lista de `{"id", "estado", "prioridad"}` con las reglas de la lección:

    - Con **límite**: lo que se ejecuta sigue (`"ejecutando"`), lo pendiente pasa a
      `"en espera de tiempo"`. Nada se cancela.
    - **Sin límite** (solo se superó la asignación): lo que se ejecuta sigue y lo pendiente sigue
      adelante pero con `prioridad="baja"` (`estado="en cola"`).

    Todo lo demás lleva `prioridad="normal"`.
    """)
    return


@app.cell
def _():
    def tras_alcanzar(trabajos, es_limite):
        # ✏️ una entrada por trabajo, sin cancelar ninguno
        return []

    ejemplo = [{"id": "a", "estado": "ejecutando"}, {"id": "b", "estado": "pendiente"}, {"id": "c", "estado": "pendiente"}]
    tras_alcanzar(ejemplo, es_limite=True)
    return (tras_alcanzar,)


@app.cell(hide_code=True)
def _(tras_alcanzar, veredicto):
    _jobs = [{"id": "a", "estado": "ejecutando"}, {"id": "b", "estado": "pendiente"}, {"id": "c", "estado": "pendiente"}]
    _con = tras_alcanzar(_jobs, True)
    _sin = tras_alcanzar(_jobs, False)

    def _bien(res, estado_pend, prio_pend):
        return ([t["id"] for t in res] == ["a", "b", "c"]
                and res[0]["estado"] == "ejecutando" and res[0]["prioridad"] == "normal"
                and all(t["estado"] == estado_pend and t["prioridad"] == prio_pend for t in res[1:]))

    veredicto(_bien(_con, "en espera de tiempo", "normal") and _bien(_sin, "en cola", "baja"),
              "Nada se cancela: con límite lo pendiente espera, sin límite sigue con menor prioridad.",
              "Debe quedar un resultado por trabajo (ninguno cancelado) con el estado y la prioridad que describe la misión.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en tu proyecto Ising, ¿preferirías para tu laboratorio un *límite* o
    solo una *asignación*? ¿Qué le pasa a una compañera que envía un trabajo urgente justo
    cuando la instancia llegó a su límite?
    """)
    return


if __name__ == "__main__":
    app.run()
