import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="1.3 · Instalar y configurar Qiskit")


@app.cell(hide_code=True)
def _():
    import contextlib
    import json
    import os
    import platform
    import struct
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    import marimo as mo
    import qiskit
    from qiskit import QuantumCircuit, transpile
    from qiskit.user_config import get_config

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    @contextlib.contextmanager
    def con_config(texto):
        """Usa `texto` como settings.conf mientras dura el bloque, como hace QISKIT_SETTINGS."""
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "settings.conf"
            ruta.write_text(texto, encoding="utf-8")
            antes = os.environ.get("QISKIT_SETTINGS")
            os.environ["QISKIT_SETTINGS"] = str(ruta)
            try:
                yield
            finally:
                if antes is None:
                    del os.environ["QISKIT_SETTINGS"]
                else:
                    os.environ["QISKIT_SETTINGS"] = antes

    mo.md("""
    # 1.3 · Instalar y configurar Qiskit: práctica

    Tres misiones: comprobar tu instalación, escribir un `settings.conf` y convertir cuadernos
    entre marimo y Jupyter. Todo corre en tu equipo. Busca el ✅.
    """)
    return (
        Path,
        QuantumCircuit,
        con_config,
        get_config,
        json,
        mo,
        platform,
        qiskit,
        struct,
        subprocess,
        sys,
        tempfile,
        transpile,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: comprueba tu instalación

    Ejecuta la celda y lee los datos de tu entorno: la versión de Qiskit, el intérprete de
    Python, si es de 64 bits y si estás dentro de un entorno virtual.
    """)
    return


@app.cell
def _(platform, qiskit, struct, sys):
    datos = {
        "qiskit": qiskit.__version__,
        "python": platform.python_version(),
        "intérprete": platform.python_implementation(),
        "bits": struct.calcsize("P") * 8,
        "entorno virtual": sys.prefix != sys.base_prefix,
    }
    datos
    return (datos,)


@app.cell(hide_code=True)
def _(datos, veredicto):
    veredicto(
        int(datos["qiskit"].split(".")[0]) >= 2 and datos["intérprete"] == "CPython" and datos["bits"] == 64,
        "Qiskit 2 o posterior, en CPython de 64 bits: justo lo que soporta.",
        "Qiskit 2 solo se soporta en CPython de 64 bits. Revisa tu entorno.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: tu `settings.conf`

    La celda usa el texto de `configuracion` como archivo de configuración y transpila un
    circuito con dos Hadamard seguidas, sin indicar nivel de optimización.

    Edita el texto para que el dibujo por defecto sea `mpl` y para que `transpile` **conserve**
    las dos Hadamard. **Antes de ejecutar, apuesta:** con el nivel que ves ahora, ¿cuántas quedan?
    """)
    return


@app.cell
def _(QuantumCircuit, con_config, get_config, transpile):
    configuracion = """[default]
circuit_drawer = text
transpile_optimization_level = 1
"""

    with con_config(configuracion):
        leida = get_config()
        dos_h = QuantumCircuit(1)
        dos_h.h(0)
        dos_h.h(0)
        puertas = dict(transpile(dos_h).count_ops())
    leida, puertas
    return leida, puertas


@app.cell(hide_code=True)
def _(leida, puertas, veredicto):
    veredicto(
        leida.get("circuit_drawer") == "mpl" and puertas == {"h": 2},
        "Con `transpile_optimization_level = 0` no se optimiza nada: las dos `h` se quedan.",
        f"Qiskit lee {leida} y deja {puertas}. Busca `mpl` y dos `h`.",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: de Jupyter a marimo y de vuelta

    Las guías de IBM y la comunidad usan Jupyter; este curso usa marimo. Escribe dos funciones
    que llamen a la línea de comandos de marimo con `subprocess`:

    - `jupyter_a_marimo(ipynb, destino)`: `marimo convert ENTRADA -o SALIDA`.
    - `marimo_a_jupyter(py, destino)`: `marimo export ipynb ENTRADA -o SALIDA`.

    Usa `sys.executable, "-m", "marimo", …` para llamar al marimo de este entorno. La
    comprobación crea un cuaderno de Jupyter pequeño, lo convierte a marimo y lo devuelve a
    Jupyter. Para usar un cuaderno de marimo en Jupyter hace falta `nbformat`, que ya está
    instalado aquí.
    """)
    return


@app.cell
def _(Path, subprocess, sys):
    def jupyter_a_marimo(ipynb: Path, destino: Path):
        """Convierte un cuaderno de Jupyter (.ipynb) en uno de marimo (.py)."""
        # ✏️ ejecuta `marimo convert` con subprocess

    def marimo_a_jupyter(py: Path, destino: Path):
        """Exporta un cuaderno de marimo (.py) como cuaderno de Jupyter (.ipynb)."""
        # ✏️ ejecuta `marimo export ipynb` con subprocess
    return jupyter_a_marimo, marimo_a_jupyter


@app.cell(hide_code=True)
def _(Path, json, jupyter_a_marimo, marimo_a_jupyter, subprocess, tempfile, veredicto):
    _cuaderno = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Hola"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["x = 1 + 2\n", "x"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    def _probar():
        with tempfile.TemporaryDirectory() as carpeta:
            d = Path(carpeta)
            (d / "a.ipynb").write_text(json.dumps(_cuaderno), encoding="utf-8")
            jupyter_a_marimo(d / "a.ipynb", d / "a.py")
            if not (d / "a.py").exists():
                return "`jupyter_a_marimo` no crea el archivo de destino."
            marimo = (d / "a.py").read_text(encoding="utf-8")
            if "marimo.App" not in marimo or "x = 1 + 2" not in marimo:
                return "El archivo de destino no es un cuaderno de marimo con el código original."
            marimo_a_jupyter(d / "a.py", d / "b.ipynb")
            if not (d / "b.ipynb").exists():
                return "`marimo_a_jupyter` no crea el archivo de destino."
            nb = json.loads((d / "b.ipynb").read_text(encoding="utf-8"))
            codigo = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
            if nb.get("nbformat") != 4 or not any("x = 1 + 2" in c for c in codigo):
                return "El archivo de vuelta no es un cuaderno de Jupyter con el código original."
        return None

    try:
        _problema = _probar()
    except (OSError, subprocess.SubprocessError, ValueError) as _e:
        _problema = f"Falló la conversión: {_e}"
    veredicto(
        _problema is None,
        "Ida y vuelta: `.ipynb` → marimo `.py` → `.ipynb`, con el código intacto.",
        _problema or "",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** el archivo de marimo es un `.py` normal. Ábrelo en un editor: ¿qué
    ventaja tiene frente a un `.ipynb` cuando varias personas lo editan con git?
    """)
    return


if __name__ == "__main__":
    app.run()
