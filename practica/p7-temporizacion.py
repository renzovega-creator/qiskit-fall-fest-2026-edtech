import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="7.3 · Temporización de circuitos")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = GenericBackendV2(2, basis_gates=["cz", "rz", "sx", "x"], seed=1)

    mo.md("""
    # 7.3 · Temporización de circuitos: práctica

    El servicio de IBM devuelve la programación de un circuito como líneas de texto:
    `rama, instrucción, canal, inicio, duración, pulso`. Aquí trabajas con ese formato sobre
    datos de ejemplo y con la programación que calcula Qiskit en local, sin cuenta. Busca el
    ✅ en cada misión.
    """)
    return QuantumCircuit, backend, generate_preset_pass_manager, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: leer los datos en bruto

    Estas líneas son las de la lección. `leer` las convierte en diccionarios. **Antes de
    ejecutar, predice:** ¿cuántos canales distintos aparecen y cuánto dura la `rz`?
    """)
    return


@app.cell
def _():
    CRUDO = """main,rz_0,Qubit 0,1393,0,shift_phase
    main,sx_0,Qubit 0,1393,9,play
    main,measure_0,Qubit 0,1402,64,play
    main,measure_0,AWGR0_0,1523,325,capture"""

    def leer(texto):
        registros = []
        for linea in texto.splitlines():
            rama, instruccion, canal, inicio, duracion, pulso = linea.strip().split(",")
            registros.append(dict(rama=rama, instruccion=instruccion, canal=canal,
                                  inicio=int(inicio), duracion=int(duracion), pulso=pulso))
        return registros

    registros = leer(CRUDO)
    for _r in registros:
        print(_r["instruccion"], "|", _r["canal"], "|", _r["inicio"], "+", _r["duracion"], "dt |", _r["pulso"])
    return (registros,)


@app.cell(hide_code=True)
def _(registros, veredicto):
    _canales = {r["canal"] for r in registros}
    _rz = next(r for r in registros if r["instruccion"] == "rz_0")
    veredicto(_canales == {"Qubit 0", "AWGR0_0"} and _rz["duracion"] == 0,
              "Dos canales (`Qubit 0` y el de lectura `AWGR0_0`), y la `rz` dura 0 dt: es un cambio de fase virtual.",
              "Deberían salir los canales `Qubit 0` y `AWGR0_0`, y la `rz` con duración 0.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuándo termina todo

    Completa dos cosas: el instante en que **termina** cada instrucción (inicio + duración,
    en dt) y el total en **nanosegundos**, con `backend.dt` (segundos por dt).
    """)
    return


@app.cell
def _(backend, registros):
    for _r in registros:
        _r["fin"] = _r["inicio"]   # ✏️ inicio + duración

    total_dt = max(r["fin"] for r in registros) - min(r["inicio"] for r in registros)
    total_ns = 0.0   # ✏️ total_dt en nanosegundos
    total_dt, total_ns
    return total_dt, total_ns


@app.cell(hide_code=True)
def _(backend, registros, total_dt, total_ns, veredicto):
    _ok_fin = all(r["fin"] == r["inicio"] + r["duracion"] for r in registros)
    _ok_ns = abs(total_ns - total_dt * backend.dt * 1e9) < 1e-6 and total_ns > 0
    veredicto(_ok_fin and _ok_ns,
              f"La última instrucción termina en {max(r['fin'] for r in registros)} dt: en total {total_dt} dt, "
              f"unos {total_ns:.0f} ns.",
              "Revisa: `fin` = `inicio` + `duracion`, y `total_ns` = `total_dt` × `backend.dt` × 1e9.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la programación de un circuito

    Qiskit calcula en local una programación que se parece a la del servicio. Transpilado
    con `scheduling_method="alap"`, cada instrucción `isa.data[i]` empieza en
    `isa.op_start_times[i]` (en dt).

    Escribe `programacion(isa, backend)`, que devuelva una lista de tuplas
    `(nombre, qubits, inicio, duración)` con la duración en dt:

    - un `delay` trae su duración en `op.duration`;
    - el resto, en `backend.target[nombre][qubits].duration` (segundos), que dividida entre
      `backend.dt` da dt.
    """)
    return


@app.cell
def _():
    def programacion(isa, backend):
        filas = []
        # ✏️ una tupla (nombre, qubits, inicio, duración en dt) por instrucción de isa.data
        return filas
    return (programacion,)


@app.cell(hide_code=True)
def _(QuantumCircuit, backend, generate_preset_pass_manager, programacion, veredicto):
    _bell = QuantumCircuit(2, 2)
    _bell.h(0)
    _bell.cx(0, 1)
    _bell.measure([0, 1], [0, 1])
    _isa = generate_preset_pass_manager(1, backend=backend, scheduling_method="alap").run(_bell)
    _filas = programacion(_isa, backend)
    _total = max((i + d for _, _, i, d in _filas), default=0)
    _esperado = _isa.estimate_duration(backend.target, unit="dt")
    _rz_ok = all(d == 0 for nombre, _, _, d in _filas if nombre == "rz")
    veredicto(len(_filas) == len(_isa.data) and abs(_total - _esperado) <= 1 and _rz_ok,
              f"{len(_filas)} instrucciones; la última termina en {_total} dt, igual que `estimate_duration`.",
              f"Salen {len(_filas)} de {len(_isa.data)} instrucciones y el total es {_total} dt "
              f"(Qiskit calcula {_esperado}). Las `rz` deben durar 0.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** esta programación local no sabe nada de difundir resultados ni de
    decidir una rama. ¿Qué parte de un circuito dinámico no aparecería en ella?
    """)
    return


if __name__ == "__main__":
    app.run()
