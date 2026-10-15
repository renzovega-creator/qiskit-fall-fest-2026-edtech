import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.7 · Depurar trabajos con NEAT")


@app.cell(hide_code=True)
def _():
    import random
    import marimo as mo
    import numpy as np
    from qiskit.circuit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit_ibm_runtime.debug_tools import Neat
    from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def circuito_espejo(n_qubits, capas):
        """Rotaciones RZ aleatorias y CX, seguidas de su inverso: cada ⟨Z⟩ ideal vale 1."""
        rng = random.Random(10)
        angulos = [[rng.random() for _ in range(n_qubits)] for _ in range(capas)]
        qc = QuantumCircuit(n_qubits)
        qubits = list(range(n_qubits))

        def pares(capa):
            return qubits[::2] if capa % 2 == 0 else qubits[1:n_qubits - 1:2]

        for capa in range(capas):
            for q in qubits:
                qc.rz(angulos[capa][q], q)
            for q in pares(capa):
                qc.cx(q, q + 1)
        for capa in reversed(range(capas)):
            for q in pares(capa):
                qc.cx(q, q + 1)
            for q in qubits:
                qc.rz(-angulos[capa][q], q)
        return qc

    def diferencia_media(ideal, ruidoso):
        """Diferencia absoluta media entre dos NeatResult, en porcentaje, por PUB."""
        return [float(np.mean(abs(i - r).vals) * 100) for i, r in zip(ideal, ruidoso)]

    mo.md("""
    # 6.7 · Depurar trabajos con NEAT: práctica

    NEAT simula tu circuito (convertido a Clifford) sin ruido y con ruido, y te da una cifra
    para comparar: la diferencia absoluta media entre los dos. Usarás el backend falso
    Sherbrooke y un circuito espejo de 6 qubits. Sin cuenta, sin cola.
    """)
    return (
        FakeSherbrooke,
        Neat,
        NoiseModel,
        SparsePauliOp,
        circuito_espejo,
        depolarizing_error,
        diferencia_media,
        generate_preset_pass_manager,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(FakeSherbrooke, SparsePauliOp, circuito_espejo, generate_preset_pass_manager):
    fake = FakeSherbrooke()
    pm = generate_preset_pass_manager(backend=fake, optimization_level=0)

    def pubs_con_capas(capas):
        """Un PUB por número de capas, con los seis ⟨Z_i⟩ ya mapeados al layout."""
        pubs = []
        for n in capas:
            isa = pm.run(circuito_espejo(6, n))
            observables = [SparsePauliOp("I" * (5 - i) + "Z" + "I" * i).apply_layout(isa.layout) for i in range(6)]
            pubs.append((isa, observables))
        return pubs
    return fake, pubs_con_capas


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el ruido crece con la profundidad

    Analiza 1, 2 y 3 capas con el modelo de ruido del backend. Antes de ejecutar, apuesta:
    ¿la diferencia media a 3 capas será menor, parecida o mayor que a 1 capa?
    """)
    return


@app.cell
def _(Neat, diferencia_media, fake, pubs_con_capas):
    analizador = Neat(fake)
    pubs_cliff = analizador.to_clifford(pubs_con_capas([1, 2, 3]))
    ideal = analizador.ideal_sim(pubs_cliff, seed_simulator=1)
    ruidoso = analizador.noisy_sim(pubs_cliff, seed_simulator=1)
    dif_backend = diferencia_media(ideal, ruidoso)
    for _capas, _d in zip([1, 2, 3], dif_backend):
        print(f"{_capas} capas: {_d:.2f} %")
    return dif_backend, ideal, pubs_cliff


@app.cell(hide_code=True)
def _(dif_backend, veredicto):
    veredicto(dif_backend[0] < dif_backend[1] < dif_backend[2],
              f"La diferencia crece con las capas: {dif_backend[0]:.1f} % → {dif_backend[2]:.1f} %. Más puertas, más sensibilidad al ruido.",
              "Debería crecer con el número de capas. ¿Cambiaste el circuito?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: tu propio modelo de ruido

    NEAT acepta un modelo de Aer. El de abajo pone un error despolarizante `p_ecr` en cada
    puerta de dos qubits del backend (`ecr`). Súbelo de 0.2 % a **2 %** y compara con el
    modelo del backend: la comprobación pide que el tuyo sea más pesimista a 3 capas.
    """)
    return


@app.cell
def _(Neat, NoiseModel, depolarizing_error, diferencia_media, fake, ideal, pubs_cliff):
    p_ecr = 0.002   # ✏️ prueba 0.02
    modelo_propio = NoiseModel()
    modelo_propio.add_all_qubit_quantum_error(depolarizing_error(p_ecr, 2), ["ecr"])
    ruidoso_propio = Neat(fake, noise_model=modelo_propio).noisy_sim(pubs_cliff, seed_simulator=1)
    dif_propio = diferencia_media(ideal, ruidoso_propio)
    print([round(d, 2) for d in dif_propio])
    return dif_propio, p_ecr


@app.cell(hide_code=True)
def _(dif_backend, dif_propio, p_ecr, veredicto):
    veredicto(dif_propio[2] > dif_backend[2],
              f"Con p_ecr = {p_ecr}, tu modelo da {dif_propio[2]:.1f} % a 3 capas frente a {dif_backend[2]:.1f} % del backend. Un modelo más duro, un diagnóstico más pesimista.",
              f"Tu modelo da {dif_propio[2]:.1f} % a 3 capas y el del backend {dif_backend[2]:.1f} %. Sube `p_ecr`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la regla de la guía

    La guía propone, según la diferencia media (en %):

    | Diferencia | Sugerencia |
    | --- | --- |
    | mayor que 90 | ninguna mitigación ayuda probablemente |
    | menor que 90 | PEA probablemente mejora |
    | menor que 80 | además, ZNE con plegado de puertas |

    Escribe `sugerencia(dif)` que devuelva la lista de técnicas: `[]`, `["PEA"]` o `["PEA", "ZNE"]`.
    """)
    return


@app.cell
def _():
    def sugerencia(dif):
        tecnicas = []
        # ✏️ añade "PEA" si dif < 90 y también "ZNE" si dif < 80
        return tecnicas
    return (sugerencia,)


@app.cell(hide_code=True)
def _(dif_backend, mo, sugerencia, veredicto):
    _ok = sugerencia(95) == [] and sugerencia(85) == ["PEA"] and sugerencia(50) == ["PEA", "ZNE"] and sugerencia(90) == []
    mo.vstack([
        veredicto(_ok,
                  "Tu regla da [] a 95 %, ['PEA'] a 85 % y ['PEA', 'ZNE'] a 50 %.",
                  "Prueba con 95, 90, 85 y 50. En 90 exacto la guía no recomienda nada."),
        mo.md("\n".join(f"- {n} capas ({d:.1f} %): {sugerencia(d)}" for n, d in zip([1, 2, 3], dif_backend))),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** con 1–3 capas la sugerencia es siempre la misma. ¿Qué te dice eso sobre
    lo que NEAT *no* mide? ¿Por qué el valor que da el simulador no garantiza lo que dará el QPU?
    """)
    return


if __name__ == "__main__":
    app.run()
