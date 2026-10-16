"""Comprueba los ejercicios de exercises/ con qgcheck.

    uv run python tools/exercises.py [lección/ejercicio ...]

Para cada ejercicio comprueba que:
  1. solution.py pasa todos los casos de check.py.
  2. starter.py se ejecuta sin error y falla algún caso: nunca llega resuelto.
  3. `needs` es verdadero. Con needs="qiskit", solution.py pasa sin qiskit_aer. Con needs="aer",
     no pasa sin él.

`needs` se lee de site/lessons/*/lesson.json, así que hay que ejecutar lessons_src/build.py antes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "lessons_src")]

from build import walk  # noqa: E402
from qgcheck import grade, spec  # noqa: E402

SITE = ROOT / "site"
NO_AER = ("qiskit_aer",)


def declared():
    """Devuelve las dependencias declaradas por los ejercicios publicados."""
    found = {}
    for f in sorted((SITE / "lessons").glob("*/lesson.json")):
        for beat in json.loads(f.read_text(encoding="utf-8"))["beats"]:
            for blk in walk(beat["scene"]):
                if blk.get("type") == "exercise":
                    found[blk["exercise"]] = blk["needs"]
    return found


def failures(result):
    """Devuelve los mensajes de los casos fallidos o el error del código."""
    if result["error"]:
        return result["error"]
    return "; ".join(f"{t['name']}: {t['message']}" for t in result["tests"] if not t["passed"]) or "sin casos"


def problems(eid, needs):
    """Devuelve los problemas del ejercicio, si los hay."""
    d = spec.folder(eid)
    if missing := spec.missing_files(eid):
        return [f"faltan {', '.join(missing)}"]
    solution = (d / "solution.py").read_text(encoding="utf-8")
    found = []
    solved = grade(eid, solution)
    if not solved["passed"]:
        found.append(f"solution.py no pasa: {failures(solved)}")
    starter = grade(eid, (d / "starter.py").read_text(encoding="utf-8"))
    if starter["error"]:
        found.append(f"starter.py falla al ejecutarse: {starter['error']}")
    elif starter["passed"]:
        found.append("starter.py ya pasa todos los casos")
    if solved["passed"]:
        without = grade(eid, solution, block=NO_AER)
        if needs == "qiskit" and not without["passed"]:
            found.append(f'needs="qiskit" pero solution.py necesita qiskit_aer: {failures(without)}')
        if needs == "aer" and without["passed"]:
            found.append('needs="aer" pero solution.py pasa sin qiskit_aer')
    return found


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    needs = declared()
    ids = sys.argv[1:] or sorted(set(needs) | set(spec.all_ids()))
    bad = 0
    for eid in ids:
        if eid not in needs:
            print(f"✗ {eid}: ninguna lección lo usa")
            bad += 1
            continue
        try:
            found = problems(eid, needs[eid])
        except ValueError as exc:
            found = [str(exc)]
        for line in found:
            print(f"✗ {eid}: {line}")
        if not found:
            print(f"✓ {eid} ({needs[eid]})")
        bad += bool(found)
    print("fallos:", bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
