"""Genera los resultados precomputados de Pages con el código Qiskit de las misiones.

    uv run python tools/demo.py

Requiere bun y las dependencias Python locales. No ejecuta código de alumnos.
"""

import argparse
import contextlib
import io
import json
import subprocess
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QISKIT_VERSION = version("qiskit")
CASES = """
import { codigo } from './site/juego/qiskit.js';
import { claveMision } from './site/demo.js';
import { RETOS } from './site/retos.js';
const cases = [];
const add = (id, params) => cases.push({ group: 'misiones', key: claveMision(id, params), code: codigo[id](params) });
for (let theta = 0; theta <= 180; theta++) add('m1', { theta, shots: 200, seed: 1 });
for (let shots = 10; shots <= 2000; shots += 10) add('m2', { shots, reps: 30, seed: 100 });
for (let e = 1; e <= 20; e++) for (const reps of [1, 2]) add('m3', { escala: e / 4, reps });
for (let shots = 10; shots <= 500; shots += 10) add('t1', { shots, reps: 20 });
for (const reto of RETOS) cases.push({ group: 'diario', key: reto.id, code: reto.code.replace('SEMILLA', '7') });
console.log(JSON.stringify(cases));
"""


def main(check: bool = False) -> None:
    spec = subprocess.run(
        ["bun", "--eval", CASES],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    cases = json.loads(spec.stdout)
    results: dict[str, dict[str, object]] = {
        "misiones": {},
        "diario": {},
    }
    for i, case in enumerate(cases, 1):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(case["code"], case["key"], "exec"), {})
        results[case["group"]][case["key"]] = json.loads(output.getvalue())
        if i % 50 == 0 or i == len(cases):
            print(f"Qiskit {QISKIT_VERSION}: {i}/{len(cases)} resultados", flush=True)
    path = ROOT / "site" / "demo-resultados.json"
    data = {
        "qiskit": QISKIT_VERSION,
        "fuente": "Código de site/juego/qiskit.js y site/retos.js; simulación local, sin hardware cuántico.",
        "semillas": {"m1": 1, "m2": 100, "diario": 7},
        **results,
    }
    rendered = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            raise SystemExit(
                "Los datos publicados difieren de Qiskit: ejecuta tools/demo.py para regenerarlos."
            )
        print(f"Verificados {len(cases)} resultados contra Qiskit {QISKIT_VERSION}.")
    else:
        path.write_text(rendered, encoding="utf-8")
        print(f"Guardados {len(cases)} resultados en {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Compara los datos publicados sin escribirlos."
    )
    main(parser.parse_args().check)
