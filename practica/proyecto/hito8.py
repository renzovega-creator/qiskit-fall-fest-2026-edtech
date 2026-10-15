import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito VIII")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_addon_obp import backpropagate
    from qiskit_addon_obp.utils.simplify import OperatorBudget
    from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # Proyecto Ising · Hito VIII: menos profundidad con OBP

    Sigues con la cadena de espines, $H = J\\sum_i Z_iZ_{i+1} + h\\sum_i X_i$, y con la pregunta de
    cómo evoluciona su magnetización. En este hito el circuito de Trotter se acorta con la
    **retropropagación de operadores** (OBP), un addon de Qiskit: las últimas capas del
    circuito pasan al observable. El circuito que se ejecuta es menos profundo, a cambio de
    un observable con más términos.

    Este cuaderno no importa los hitos anteriores: recalcula lo que necesita de ellos y
    todo corre en tu equipo, con el dispositivo simulado `FakeFez`.
    """)
    return (AerEstimator, FakeFez, OperatorBudget, QuantumCircuit, SparsePauliOp, Statevector,
            backpropagate, combine_slices, expm, generate_preset_pass_manager, mo, np, plt,
            slice_by_gate_types, veredicto)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el punto de partida

    Recalculas tres resultados de hitos anteriores: el Hamiltoniano y el circuito de $N$ pasos
    (hito II), la magnetización de Trotter frente a la exacta (hitos II y IV) y la profundidad
    del circuito transpilado para `FakeFez` (hito III). Con 6 espines y 4 pasos, la
    profundidad que sale es la que vas a reducir.
    """)
    return


@app.cell
def _(FakeFez, QuantumCircuit, SparsePauliOp, Statevector, combine_slices, expm,
      generate_preset_pass_manager, np, slice_by_gate_types):
    n, J, h, dt, pasos = 6, 1.0, 0.5, 0.2, 4

    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)], num_qubits=n)
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)

    def trotter(k):
        """k pasos de primer orden: ZZ en pares pares, ZZ en pares impares, X en todos."""
        qc = QuantumCircuit(n)
        for _ in range(k):
            for a in range(0, n - 1, 2):
                qc.rzz(2 * J * dt, a, a + 1)
            for a in range(1, n - 1, 2):
                qc.rzz(2 * J * dt, a, a + 1)
            for a in range(n):
                qc.rx(2 * h * dt, a)
        return qc

    def valor(circ, obs):
        return float(np.real(Statevector(circ).expectation_value(obs)))

    def unir(capas_):
        return combine_slices(capas_, include_barriers=False) if capas_ else QuantumCircuit(n)

    fez = FakeFez()
    pm = generate_preset_pass_manager(optimization_level=1, backend=fez, seed_transpiler=1)

    def profundidad_isa(circ):
        return pm.run(circ).depth()

    circuito = trotter(pasos)
    capas = slice_by_gate_types(circuito)   # 3 capas por paso: ZZ pares, ZZ impares, X

    psi0 = np.zeros(2**n)
    psi0[0] = 1
    psi_t = expm(-1j * H.to_matrix() * dt * pasos) @ psi0
    m_exacta = float(np.real(psi_t.conj() @ M.to_matrix() @ psi_t))
    m_trotter = valor(circuito, M)
    prof_completa = profundidad_isa(circuito)

    print(f"magnetización exacta {m_exacta:.4f} · Trotter {m_trotter:.4f}")
    print(f"profundidad lógica {circuito.depth()} → transpilada para FakeFez {prof_completa}")
    return (M, capas, circuito, fez, m_exacta, m_trotter, pm, prof_completa, profundidad_isa,
            slice_by_gate_types, trotter, unir, valor)


@app.cell(hide_code=True)
def _(circuito, m_exacta, m_trotter, prof_completa, veredicto):
    veredicto(abs(m_exacta - m_trotter) < 0.01 and prof_completa > circuito.depth(),
              f"Trotter se separa {abs(m_exacta - m_trotter):.4f} de lo exacto, y transpilar multiplica la "
              f"profundidad por {prof_completa / circuito.depth():.1f}.",
              "Debería haber menos de 0.01 de diferencia con la evolución exacta, y la profundidad transpilada "
              "mayor que la lógica.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuántas capas absorbe OBP

    `backpropagate(M, capas[-k:])` lleva las últimas `k` capas al observable $M$, empezando por la
    final. Cada capa absorbida quita profundidad, pero el observable gana términos, y cada
    término es una medición más. Elige `k` para que:

    - la profundidad transpilada baje **al menos un 25 %**,
    - el observable no pase de **100 términos**,
    - el valor esperado siga igual (OBP sin truncar es exacto).
    """)
    return


@app.cell
def _(M, backpropagate, capas, profundidad_isa, unir, valor):
    k = 0   # ✏️ cuántas de las 12 capas finales absorbe OBP

    if k:
        obs_k, resto_k, _meta = backpropagate(M, capas[-k:])
        corto_k = unir(capas[:-k] + list(resto_k))
    else:
        obs_k, corto_k = M, unir(capas)

    print(f"k = {k}: {len(obs_k)} términos · profundidad transpilada {profundidad_isa(corto_k)} · "
          f"valor {valor(corto_k, obs_k):.6f}")
    return corto_k, k, obs_k


@app.cell(hide_code=True)
def _(M, circuito, corto_k, k, obs_k, prof_completa, profundidad_isa, valor, veredicto):
    _p = profundidad_isa(corto_k)
    _mismo = abs(valor(corto_k, obs_k) - valor(circuito, M)) < 1e-6
    veredicto(_p <= 0.75 * prof_completa and len(obs_k) <= 100 and _mismo,
              f"k = {k}: profundidad {prof_completa} → {_p} ({1 - _p / prof_completa:.0%} menos) con {len(obs_k)} términos.",
              f"Con k = {k}: profundidad {_p} (hace falta ≤ {int(0.75 * prof_completa)}), {len(obs_k)} términos "
              f"(máximo 100), mismo valor: {'sí' if _mismo else 'no'}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el ahorro para cualquier número de pasos

    Escribe `ahorro(pasos, limite=100)`. Debe construir el circuito de `pasos` pasos, dividirlo
    en capas y llamar a `backpropagate` con todas las capas y
    `operator_budget=OperatorBudget(max_paulis=limite)`, para que OBP se detenga solo.
    Devuelve un diccionario con:

    - `prof_sin` y `prof_con`: profundidad transpilada del circuito original y del que queda;
    - `terminos`: términos del observable nuevo;
    - `error`: diferencia absoluta entre los valores esperados con y sin OBP.

    Usa `slice_by_gate_types`, `unir` (que junta las capas que quedan) y `profundidad_isa`.
    """)
    return


@app.cell
def _(M, OperatorBudget, backpropagate, profundidad_isa, slice_by_gate_types, trotter, unir, valor):
    def ahorro(pasos, limite=100):
        # ✏️ circuito → capas → backpropagate con presupuesto → medidas
        return None
    return (ahorro,)


@app.cell(hide_code=True)
def _(ahorro, profundidad_isa, trotter, veredicto):
    _r = {p: ahorro(p) for p in (2, 4, 6)}
    _ok = all(isinstance(v, dict) for v in _r.values())
    if _ok:
        _ok = (all(v["terminos"] <= 100 and v["error"] < 1e-6 and v["prof_con"] < v["prof_sin"] for v in _r.values())
               and _r[4]["prof_sin"] == profundidad_isa(trotter(4)))
    _resumen = ", ".join(f"{p} pasos: {v['prof_sin']} → {v['prof_con']}" for p, v in _r.items()) if _ok else ""
    veredicto(_ok,
              f"Profundidad transpilada sin OBP → con OBP (100 términos): {_resumen}.",
              "`ahorro(p)` debe devolver un diccionario con `prof_sin`, `prof_con`, `terminos` y `error`; "
              "con `terminos` ≤ 100, `error` < 1e-6 y `prof_con` menor que `prof_sin`.")
    return


@app.cell(hide_code=True)
def _(mo):
    limite = mo.ui.slider(30, 300, step=10, value=100, label="límite de términos del observable", show_value=True)
    mo.vstack([mo.md("### Explora\nMueve el límite: más términos permiten absorber más capas."), limite])
    return (limite,)


@app.cell(hide_code=True)
def _(ahorro, limite, mo, plt):
    _pasos = list(range(2, 9))
    _datos = [ahorro(p, limite.value) for p in _pasos]
    if all(isinstance(d, dict) for d in _datos):
        _fig, _ax = plt.subplots(figsize=(6, 3))
        _ax.plot(_pasos, [d["prof_sin"] for d in _datos], "o-", label="sin OBP")
        _ax.plot(_pasos, [d["prof_con"] for d in _datos], "o-", label=f"con OBP (≤ {limite.value} términos)")
        _ax.set_xlabel("pasos de Trotter")
        _ax.set_ylabel("profundidad transpilada")
        _ax.legend()
        _salida = mo.vstack([_fig, mo.md("Términos del observable: " + ", ".join(str(d["terminos"]) for d in _datos))])
    else:
        _salida = mo.md("_Completa la misión 🔴 para ver la curva._")
    _salida
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ¿Se acerca más a lo exacto con ruido?

    La profundidad menor solo vale la pena si el resultado mejora. Esta celda ejecuta, con el
    ruido de `FakeFez`, el circuito completo y el reducido por tu `k` de la misión 🟡 (4 pasos),
    y compara cada uno con la magnetización de Trotter exacta. Usa una precisión de 0.005 para
    que el ruido de muestreo no tape la diferencia, y tarda unos veinte segundos.
    """)
    return


@app.cell(hide_code=True)
def _(AerEstimator, M, circuito, corto_k, fez, k, mo, obs_k, pm, valor, veredicto):
    _est = AerEstimator.from_backend(fez, options={"backend_options": {"seed_simulator": 1}})
    _exacto = valor(circuito, M)

    def _ruidoso(circ, obs):
        _isa = pm.run(circ)
        return float(_est.run([(_isa, obs.apply_layout(_isa.layout))], precision=0.005).result()[0].data.evs)

    _e_completo = abs(_ruidoso(circuito, M) - _exacto)
    _e_corto = abs(_ruidoso(corto_k, obs_k) - _exacto) if k else _e_completo
    _tabla = mo.md(f"""
    | circuito | error con ruido |
    | --- | --- |
    | completo | {_e_completo:.4f} |
    | con OBP, k = {k} | {_e_corto:.4f} |
    """)
    _v = veredicto(k > 0 and _e_corto < _e_completo,
                   "El circuito más corto acumula menos ruido: su magnetización queda más cerca de la exacta.",
                   "Elige un `k` mayor que 0 en la misión 🟡 para ver cómo cambia el error." if not k
                   else "Con este `k` el error no baja: prueba otro valor.")
    mo.vstack([_tabla, _v])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** con el límite fijo, ¿crece o se mantiene el ahorro absoluto de profundidad
    al agregar pasos? ¿Y el relativo? ¿En qué se parece esto a lo que hace AQC-Tensor con
    las primeras capas?
    """)
    return


if __name__ == "__main__":
    app.run()
