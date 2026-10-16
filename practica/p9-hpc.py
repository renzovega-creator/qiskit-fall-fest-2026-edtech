import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="9.3 · HPC: QRMI y Slurm")


@app.cell(hide_code=True)
def _():
    import json
    import re

    import marimo as mo

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 9.3 · HPC: QRMI y Slurm: práctica

    El plugin SPANK cruza lo que **pide el usuario** (`--qpu=...`) con lo que **define el
    administrador** (`qrmi_config.json`) y deja el resultado en variables de entorno que
    lee QRMI. Aquí repites ese cruce en Python con una configuración de ejemplo. No hace
    falta Slurm, ni cuenta, ni red.
    """)
    return json, mo, re, veredicto


@app.cell
def _(json):
    config = json.loads("""
    {"resources": [
      {"name": "my_local_qpu", "type": "direct-access", "environment": {}},
      {"name": "ibm_fez", "type": "qiskit-runtime-service",
       "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"}}
    ]}
    """)
    script = """#!/bin/bash
#SBATCH --time=100
#SBATCH --gres=qpu:3
#SBATCH --qpu=my_local_qpu,ibm_fez,ibm_marrakesh
srun python mi_programa.py"""
    return config, script


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: qué recibe el trabajo

    El script pide tres QPUs y el administrador definió dos. Lee cómo se cruzan las dos
    listas: lo que no está definido se ignora.
    """)
    return


@app.cell
def _(config, re, script):
    pedidos = re.search(r"--qpu=(\S+)", script).group(1).split(",")
    definidos = {r["name"]: r for r in config["resources"]}
    recursos = [nombre for nombre in pedidos if nombre in definidos]
    recursos
    return definidos, pedidos, recursos


@app.cell(hide_code=True)
def _(pedidos, recursos, veredicto):
    veredicto(recursos == ["my_local_qpu", "ibm_fez"],
              f"Pediste {len(pedidos)} y el trabajo recibe {len(recursos)}: `ibm_marrakesh` no está en `qrmi_config.json`, así que se ignora.",
              f"Salió {recursos}. Deberían ser `my_local_qpu` e `ibm_fez`, en el orden en que se pidieron.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: el administrador define otro QPU

    Como administrador, añade `ibm_marrakesh` a `config_admin`. Es un recurso del servicio
    de IBM (`qiskit-runtime-service`) y tu plan es Open, que no admite sesiones: pon en su
    `environment` la variable `QRMI_IBM_QRS_SESSION_MODE` con el valor `"batch"`.
    """)
    return


@app.cell
def _(config, json):
    config_admin = json.loads(json.dumps(config))   # copia
    # ✏️ añade el recurso ibm_marrakesh a config_admin["resources"]
    config_admin["resources"]
    return (config_admin,)


@app.cell(hide_code=True)
def _(config_admin, pedidos, veredicto):
    _por_nombre = {r["name"]: r for r in config_admin["resources"]}
    _marrakesh = _por_nombre.get("ibm_marrakesh", {})
    _recibe = [n for n in pedidos if n in _por_nombre]
    veredicto(len(_recibe) == 3
              and _marrakesh.get("type") == "qiskit-runtime-service"
              and _marrakesh.get("environment", {}).get("QRMI_IBM_QRS_SESSION_MODE") == "batch",
              "Ahora el trabajo recibe los tres QPUs, y el de IBM usa el modo lote.",
              f"El trabajo recibiría {len(_recibe)} de 3, o a `ibm_marrakesh` le falta el tipo o el modo `batch`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: las variables que fija el plugin

    El plugin deja dos variables que lee QRMI, ambas listas separadas por comas, **sin** los
    recursos no definidos:

    - `SLURM_JOB_QPU_RESOURCES`: los nombres, en el orden pedido.
    - `SLURM_JOB_QPU_TYPES`: el tipo de cada uno.

    Además, cada variable del `environment` de un recurso se exporta con el nombre del
    recurso como prefijo: `ibm_fez_QRMI_IBM_QRS_SESSION_MODE`.

    Escribe `entorno(qpu, config)`, donde `qpu` es el texto de `--qpu` (por ejemplo
    `"ibm_fez,otro"`), y devuelve un diccionario con esas variables.
    """)
    return


@app.cell
def _():
    def entorno(qpu, config):
        # ✏️ tu código aquí
        return {}
    return (entorno,)


@app.cell(hide_code=True)
def _(config, entorno, veredicto):
    try:
        _env = entorno("ibm_fez,ibm_kyiv,my_local_qpu", config)
        _ok = (_env.get("SLURM_JOB_QPU_RESOURCES") == "ibm_fez,my_local_qpu"
               and _env.get("SLURM_JOB_QPU_TYPES") == "qiskit-runtime-service,direct-access"
               and _env.get("ibm_fez_QRMI_IBM_QRS_SESSION_MODE") == "batch"
               and len([k for k in _env if k.endswith("QRMI_IBM_QRS_SESSION_MODE")]) == 1)
        _no = f"Salió {_env}. Revisa el orden, que `ibm_kyiv` no esté, y el prefijo de la variable."
    except Exception as e:
        _ok, _no = False, f"`entorno` falla con {type(e).__name__}."
    veredicto(_ok,
              "Tu `entorno` filtra los recursos sin definir y prefija las variables con el nombre del QPU.",
              _no)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si `ibm_marrakesh` se ignora en silencio, ¿qué ventaja tiene para un
    usuario que su código lea `SLURM_JOB_QPU_RESOURCES` en lugar de fijar el nombre del
    backend? ¿Y qué riesgo?
    """)
    return


if __name__ == "__main__":
    app.run()
