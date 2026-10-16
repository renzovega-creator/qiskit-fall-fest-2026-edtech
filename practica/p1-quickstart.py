import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="1.4 · Tu primer circuito")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorSampler

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def conteos(qc, shots=1024):
        return StatevectorSampler(seed=7).run([qc], shots=shots).result()[0].data.meas.get_counts()

    mo.md("""
    # 1.4 · Tu primer circuito: práctica

    Una misión con una comprobación que se actualiza sola al cambiar el código:
    busca el ✅.
    """)
    return QuantumCircuit, conteos, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: el estado de Bell

    Ejecuta el circuito de la lección y mira los conteos. No tienes que cambiar nada:
    lee cada línea y asegúrate de entender qué hace.
    """)
    return


@app.cell
def _(QuantumCircuit, conteos):
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()

    conteos_bell = conteos(bell)
    conteos_bell
    return (conteos_bell,)


@app.cell(hide_code=True)
def _(conteos_bell, veredicto):
    veredicto(set(conteos_bell) == {"00", "11"},
              "Solo aparecen `00` y `11`: los qubits están perfectamente correlacionados.",
              "Deberían aparecer solo `00` y `11`. ¿Cambiaste algo del circuito?")
    return


if __name__ == "__main__":
    app.run()
