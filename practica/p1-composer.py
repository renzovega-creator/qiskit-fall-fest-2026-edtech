import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="1.5 · IBM Quantum Composer")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import qasm2
    from qiskit.primitives import StatevectorSampler
    from qiskit.quantum_info import Statevector

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    def estado(texto):
        """Estado que prepara un programa OpenQASM 2.0, sin las mediciones finales."""
        qc = qasm2.loads(texto)
        return Statevector(qc.remove_final_measurements(inplace=False))

    mo.md("""
    # 1.5 · IBM Quantum Composer: práctica

    Composer genera y acepta OpenQASM 2.0. Aquí lo escribes tú y lo ejecutas en tu equipo con
    `qiskit.qasm2`: lo que pegarías en el editor de código de Composer. Busca el ✅.
    """)
    return Statevector, StatevectorSampler, estado, mo, np, qasm2, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: una puerta propia

    El programa OpenQASM de la lección define la puerta `bell` y la usa. Ejecútalo y lee los
    conteos: la puerta propia aparece como una sola instrucción del circuito.
    """)
    return


@app.cell
def _(StatevectorSampler, qasm2):
    bell_qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate bell a, b { h a; cx a, b; }
bell q[0], q[1];
measure q -> c;
"""
    circuito_bell = qasm2.loads(bell_qasm)
    conteos_bell = StatevectorSampler(seed=3).run([circuito_bell], shots=1024).result()[0].data.c.get_counts()
    conteos_bell, dict(circuito_bell.count_ops())
    return circuito_bell, conteos_bell


@app.cell(hide_code=True)
def _(circuito_bell, conteos_bell, veredicto):
    veredicto(
        set(conteos_bell) == {"00", "11"} and "bell" in circuito_bell.count_ops(),
        "Solo `00` y `11`, y `bell` es una instrucción propia del circuito.",
        "Deberían salir solo `00` y `11`, con `bell` como instrucción. ¿Cambiaste el programa?",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: una fase que la vista de probabilidades no ve

    Este programa pone una Hadamard en cada qubit y una `cz`. La `cz` cambia el signo de la
    amplitud de $|11\\rangle$ y no toca ninguna probabilidad.

    Cambia la línea de la `cz` por una fase controlada `cu1(pi/2)`. **Antes de ejecutar,
    apuesta:** ¿cambian las probabilidades? ¿Y la amplitud de $|11\\rangle$?
    """)
    return


@app.cell
def _(estado):
    vistas_qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cz q[0],q[1];
"""
    sv_vistas = estado(vistas_qasm)
    sv_vistas.probabilities_dict(), sv_vistas.data[3]
    return (sv_vistas,)


@app.cell(hide_code=True)
def _(np, sv_vistas, veredicto):
    veredicto(
        np.allclose(sv_vistas.probabilities(), 0.25) and np.isclose(sv_vistas.data[3], 0.5j),
        "Las cuatro probabilidades siguen en 1/4, pero la amplitud de `11` ahora es $i/2$: fase de 90°.",
        "Busca probabilidades de 1/4 y una amplitud de $|11\\rangle$ igual a $i/2$. Prueba con `cu1(pi/2)`.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: tu puerta `ghz`

    Define en OpenQASM una puerta `ghz a, b, c` que prepare el estado GHZ de tres qubits con
    una Hadamard y dos CNOT. El programa ya la usa sobre los tres qubits de `q`: tú escribes
    el cuerpo de la puerta, entre las llaves.
    """)
    return


@app.cell
def _(estado):
    ghz_qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
gate ghz a, b, c { }  // ✏️ escribe aquí el cuerpo
ghz q[0], q[1], q[2];
"""
    sv_ghz = estado(ghz_qasm)
    sv_ghz.probabilities_dict()
    return (sv_ghz,)


@app.cell(hide_code=True)
def _(np, sv_ghz, veredicto):
    veredicto(
        np.allclose(sv_ghz.probabilities([0, 1, 2]), [0.5, 0, 0, 0, 0, 0, 0, 0.5]),
        "Tu `ghz` prepara $\\tfrac{1}{\\sqrt2}(|000\\rangle+|111\\rangle)$.",
        "Deberían quedar solo `000` y `111`, con probabilidad 1/2 cada una.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en la misión 🟡 las probabilidades no cambiaron, pero la amplitud sí.
    ¿Qué visualización de Composer te dejaría ver esa diferencia?
    """)
    return


if __name__ == "__main__":
    app.run()
