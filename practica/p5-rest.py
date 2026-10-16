import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.7 · La API REST")


@app.cell(hide_code=True)
def _():
    import json
    import os

    import marimo as mo
    import qiskit.qasm3
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    bell = QuantumCircuit(2, 2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure([0, 1], [0, 1])
    isa = pm.run(bell)

    mo.md("""

    Tres misiones para preparar el cuerpo de los trabajos y leer sus resultados, **sin enviar
    nada**: todo se construye y se comprueba en tu equipo. La última celda es un interruptor
    opcional para probar tu clave API de verdad. No hace nada si no lo activas.
    """)
    return (
        QuantumCircuit,
        Sampler,
        SparsePauliOp,
        backend,
        isa,
        json,
        mo,
        os,
        pm,
        qiskit,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el cuerpo de un trabajo de Sampler

    Un Bell transpilado para el procesador falso se exporta con `qasm3.dumps` y se coloca en el
    PUB `[circuito, parámetros, disparos]`. Antes de ejecutar, predice: ¿qué valor llevará la
    clave `params` para un circuito sin parámetros: `None`, `{}` o `[]`?
    """)
    return


@app.cell
def _(isa, json, qiskit):
    qasm = qiskit.qasm3.dumps(isa)
    cuerpo_sampler = {
        "program_id": "sampler",
        "backend": "ibm_fez",
        "params": {"pubs": [[qasm, None, 500]]},
    }
    print(qasm)
    print(json.dumps(cuerpo_sampler["params"]["pubs"][0][1:]))
    return (cuerpo_sampler,)


@app.cell(hide_code=True)
def _(cuerpo_sampler, json, veredicto):
    _pub = cuerpo_sampler["params"]["pubs"][0]
    veredicto(_pub[0].startswith("OPENQASM 3") and _pub[1] is None and _pub[2] == 500
              and json.loads(json.dumps(cuerpo_sampler)) == cuerpo_sampler,
              "El cuerpo es JSON válido: circuito en OpenQASM 3, `None` (se envía como `null`) y 500 disparos.",
              "El PUB debe ser `[texto OpenQASM 3, None, 500]` y todo el cuerpo debe poder serializarse a JSON.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: leer `samples` como cadenas de bits

    Los resultados de Sampler por REST vienen como números hexadecimales, uno por disparo:
    `'0x2'`. La celda ejecuta el mismo Bell en local, convierte cada disparo a hexadecimal y
    lo decodifica de vuelta. Falta algo: `'0x1'` debería ser `'01'`, no `'1'`. Arregla
    `decodificar` para que rellene con ceros hasta `n_bits` y los conteos coincidan con los
    que da `get_counts()`.
    """)
    return


@app.cell
def _(Sampler, backend, isa):
    _sampler = Sampler(mode=backend)
    _sampler.options.default_shots = 300
    _sampler.options.simulator.seed_simulator = 5
    _registro = _sampler.run([isa]).result()[0].data.c

    # Lo que devolvería el servicio: un hexadecimal por disparo.
    muestras = [hex(int(_bits, 2)) for _bits in _registro.get_bitstrings()]

    def decodificar(muestras, n_bits):
        conteos = {}
        for h in muestras:
            bits = format(int(h, 16), "b")   # ✏️ rellena con ceros hasta n_bits
            conteos[bits] = conteos.get(bits, 0) + 1
        return conteos

    esperados = _registro.get_counts()
    decodificados = decodificar(muestras, 2)
    print(muestras[:8], "…")
    decodificados
    return decodificados, esperados


@app.cell(hide_code=True)
def _(decodificados, esperados, veredicto):
    veredicto(decodificados == esperados,
              f"Los conteos coinciden con `get_counts()`: {dict(sorted(decodificados.items()))}.",
              f"Salió {dict(sorted(decodificados.items()))}; debería ser {dict(sorted(esperados.items()))}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el cuerpo de un trabajo de Estimator

    Escribe `cuerpo_estimator(isa, observable, opciones)`. Debe devolver el diccionario del
    trabajo con `program_id`, `backend` (`"ibm_fez"`), y en `params`, la lista `pubs` con un
    PUB `[qasm, observable, None]` y las `options`.

    Dos trampas:

    1. El observable debe pasar por `apply_layout(isa.layout)`: el circuito transpilado tiene
       las cinco posiciones del procesador.
    2. En JSON, el observable es un diccionario `{cadena de Pauli: coeficiente}` y los
       coeficientes de `SparsePauliOp` son complejos: JSON no los admite. Convierte a `float`.
    """)
    return


@app.cell
def _(SparsePauliOp, isa, qiskit):
    def cuerpo_estimator(isa, observable, opciones):
        return {}   # ✏️ program_id, backend, params con pubs y options

    observable_zz = SparsePauliOp("ZZ")
    opciones_zne = {"resilience": {"zne_mitigation": True, "zne": {"noise_factors": [1, 3, 5]}}}
    return cuerpo_estimator, observable_zz, opciones_zne


@app.cell(hide_code=True)
def _(cuerpo_estimator, isa, json, observable_zz, opciones_zne, qiskit, veredicto):
    _cuerpo = cuerpo_estimator(isa, observable_zz, opciones_zne)
    try:
        _texto = json.dumps(_cuerpo)
        _pub = _cuerpo["params"]["pubs"][0]
        _etiquetas = list(_pub[1])
        _ok = (_cuerpo["program_id"] == "estimator" and _cuerpo["backend"] == "ibm_fez"
               and _cuerpo["params"]["options"] == opciones_zne
               and qiskit.qasm3.loads(_pub[0]).num_qubits >= 2
               and _etiquetas == ["IIIZZ"] and _pub[1]["IIIZZ"] == 1.0 and _pub[2] is None)
        _causa = "revisa el observable (`apply_layout`, 5 letras) y las claves del cuerpo."
    except (KeyError, IndexError, TypeError) as _e:
        _ok, _causa = False, f"el cuerpo no tiene la estructura esperada ({type(_e).__name__})."
    veredicto(_ok,
              "El cuerpo es JSON válido y el observable `IIIZZ` ya refleja el *layout* del procesador.",
              _causa)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ⚙️ Opcional: tu clave API de verdad

    Activa el interruptor para pedir un token portador y consultar `usage`. Necesita las
    variables de entorno `IQP_API_TOKEN` y `IQP_CRN` y red; si falta alguna, la celda lo dice
    y no hace nada.
    """)
    return


@app.cell
def _(mo):
    consulta_real = mo.ui.switch(label="⚠️ Consultar el servicio real (solo lectura)")
    consulta_real
    return (consulta_real,)


@app.cell
def _(consulta_real, mo, os):
    mo.stop(not consulta_real.value, mo.md("Interruptor apagado: no se envía ninguna petición."))
    _clave, _crn = os.environ.get("IQP_API_TOKEN"), os.environ.get("IQP_CRN")
    mo.stop(not (_clave and _crn), mo.md("Faltan `IQP_API_TOKEN` o `IQP_CRN`: no se envía ninguna petición."))

    import requests

    try:
        _iam = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={_clave}",
            timeout=30,
        )
        mo.stop(not _iam.ok, mo.md(f"IAM rechazó la clave (HTTP {_iam.status_code}): no se consulta `usage`."))
        _uso = requests.get(
            "https://quantum.cloud.ibm.com/api/v1/usage",
            headers={"Authorization": f"Bearer {_iam.json()['access_token']}", "Service-CRN": _crn},
            timeout=30,
        )
    except (requests.RequestException, ValueError, KeyError) as _e:
        mo.stop(True, mo.md(f"No se pudo completar la petición ({type(_e).__name__}): no se muestra nada."))
    mo.md(f"`GET /usage` → **{_uso.status_code}**")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el token portador caduca en una hora, pero la clave API no. ¿Qué
    guardarías en un archivo de configuración y qué pedirías de nuevo en cada ejecución?
    """)
    return


if __name__ == "__main__":
    app.run()
