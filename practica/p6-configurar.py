import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="6.4 · Configurar el ruido en Estimator y Sampler")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.executor_sampler import Sampler
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 6.4 · Configurar el ruido: práctica

    Las opciones de las primitivas se validan en tu equipo, sin enviar nada. Un backend falso
    basta para crear `Estimator` y `Sampler` y comprobar qué opciones admiten. Sin cuenta.
    """)
    return Estimator, FakeManilaV2, Sampler, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: lo que hay por defecto

    Crea un `Estimator` sin pedir nada y lee sus opciones. Antes de ejecutar, apuesta: ¿qué
    `resilience_level` trae? Fíjate también en `measure_mitigation`: `None` significa «que lo
    decida el nivel».
    """)
    return


@app.cell
def _(Estimator, FakeManilaV2):
    fake = FakeManilaV2()
    estimator = Estimator(fake)
    nivel_por_defecto = estimator.options.resilience_level
    print("resilience_level:", nivel_por_defecto)
    print("measure_mitigation:", estimator.options.resilience.measure_mitigation)
    print("zne_mitigation:", estimator.options.resilience.zne_mitigation)
    return fake, nivel_por_defecto


@app.cell(hide_code=True)
def _(nivel_por_defecto, veredicto):
    veredicto(nivel_por_defecto == 1,
              "El nivel por defecto es 1: TREX. Pedir «nada» no es lo mismo que no mitigar.",
              f"Lees {nivel_por_defecto}. Mira `estimator.options.resilience_level`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: TREX y ZNE sin nivel

    Parte del nivel 0 (sin mitigación) y activa **a mano** TREX y ZNE con los factores de
    ruido 1, 3 y 5. Las opciones explícitas se aplican encima del nivel base. Prueba también
    un valor inválido, como `resilience_level = 7`, para ver el error de validación.
    """)
    return


@app.cell
def _(Estimator, fake):
    estimator_2 = Estimator(fake, options={"resilience_level": 0})
    opciones = estimator_2.options
    # ✏️ activa TREX (measure_mitigation), ZNE (zne_mitigation) y zne.noise_factors = (1, 3, 5)
    opciones.resilience
    return (opciones,)


@app.cell(hide_code=True)
def _(opciones, veredicto):
    _r = opciones.resilience
    veredicto(opciones.resilience_level == 0 and _r.measure_mitigation is True and _r.zne_mitigation is True
              and tuple(_r.zne.noise_factors) == (1.0, 3.0, 5.0),
              "Nivel 0 con TREX y ZNE (1, 3, 5) activados por separado: las opciones explícitas mandan.",
              "Faltan opciones: `measure_mitigation = True`, `zne_mitigation = True` y `zne.noise_factors = (1, 3, 5)`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: `preparar(primitiva, tecnicas)`

    Escribe una función que devuelva un `Estimator` o un `Sampler` configurado con un
    conjunto de técnicas: `"dd"` (desacoplamiento), `"twirling"` (puertas), `"trex"` y
    `"zne"`. Un `Sampler` no tiene mitigación de expectativas: si le pides `"trex"` o
    `"zne"`, lanza `ValueError`.
    """)
    return


@app.cell
def _(Estimator, Sampler, fake):
    def preparar(primitiva, tecnicas):
        p = Estimator(fake) if primitiva == "estimator" else Sampler(fake)
        if "dd" in tecnicas:
            p.options.dynamical_decoupling.enable = True
        # ✏️ twirling de puertas, TREX y ZNE (y el error para Sampler)
        return p
    return (preparar,)


@app.cell(hide_code=True)
def _(preparar, veredicto):
    def _lanza():
        try:
            preparar("sampler", {"trex"})
        except ValueError:
            return True
        return False
    _e = preparar("estimator", {"dd", "twirling", "trex", "zne"}).options
    _s = preparar("sampler", {"dd", "twirling"}).options
    _vacio = preparar("estimator", set()).options
    veredicto(_e.dynamical_decoupling.enable is True and _e.twirling.enable_gates is True
              and _e.resilience.measure_mitigation is True and _e.resilience.zne_mitigation is True
              and _s.twirling.enable_gates is True and _lanza()
              and not _vacio.resilience.zne_mitigation,
              "Estimator admite las cuatro técnicas; Sampler solo DD y twirling, y rechaza TREX.",
              "Revisa: el Estimator debe activar las cuatro; el Sampler, solo `dd` y `twirling`, y `preparar('sampler', {'trex'})` debe lanzar ValueError.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el nivel por defecto ya mitiga la lectura sin que lo pidas. Si comparas
    «sin mitigar» con «nivel por defecto», ¿qué estarías comparando de verdad? ¿Cómo
    pedirías una ejecución *sin* ninguna mitigación?
    """)
    return


if __name__ == "__main__":
    app.run()
