"""Pruebas del formato de ejercicios, del corrector y de lo que build.py publica.

    uv run pytest tests/exercises_test.py

Cada ejercicio de exercises/ se corrige con su solución (pasa) y con una solución equivocada (falla
con un mensaje útil). No necesitan red.
"""
import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "lessons_src")]

import build  # noqa: E402
from qgcheck import grade, spec  # noqa: E402


def load_tool():
    tool = importlib.util.spec_from_file_location("exercises_tool", ROOT / "tools" / "exercises.py")
    module = importlib.util.module_from_spec(tool)
    tool.loader.exec_module(module)
    return module


exercises_tool = load_tool()

REAL = spec.all_ids()

GHZ_WITHOUT_CHAIN = """
from qiskit import QuantumCircuit
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc
"""

GHZ_WITHOUT_MEASURE = """
from qiskit import QuantumCircuit
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    return qc
"""

# (ejercicio, código equivocado, texto esperado en algún mensaje de fallo)
WRONG = [
    ("p1-quickstart/bell-distinto",
     "from qiskit import QuantumCircuit\nanti = QuantumCircuit(2)\nanti.h(0)\nanti.cx(0, 1)\nanti.z(1)\nanti.measure_all()\n",
     "Salen ['00', '11']"),
    ("p1-quickstart/ghz", GHZ_WITHOUT_CHAIN, "Con n = 3 salen ['000', '011']"),
    ("p1-quickstart/ghz", GHZ_WITHOUT_MEASURE, "falta `measure_all()`"),
    ("p2-control-clasico/siempre-uno",
     textwrap.dedent("""
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
        q, c = QuantumRegister(1, "q"), ClassicalRegister(1, "c")
        siempre_uno = QuantumCircuit(q, c)
        siempre_uno.h(q[0])
        siempre_uno.measure(q[0], c[0])
        siempre_uno.x(q[0])
        siempre_uno.measure(q[0], c[0])
     """),
     "Salen {"),
    ("p2-control-clasico/hasta-uno",
     textwrap.dedent("""
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
        def hasta_uno():
            q, c = QuantumRegister(1, "q"), ClassicalRegister(1, "c")
            qc = QuantumCircuit(q, c)
            qc.h(q[0])
            qc.measure(q[0], c[0])
            with qc.while_loop((c, 0)):
                qc.x(q[0])
                qc.measure(q[0], c[0])
            return qc
     """),
     "no de una puerta X"),
]


def read(exercise_id, name):
    return (spec.folder(exercise_id) / name).read_text(encoding="utf-8")


def failed(result):
    return [t for t in result["tests"] if not t["passed"]]


@pytest.mark.parametrize("exercise_id", REAL)
def test_solution_passes(exercise_id):
    result = grade(exercise_id, read(exercise_id, "solution.py"))
    assert result["passed"], result
    assert result["tests"] and all(t["passed"] and t["message"] is None for t in result["tests"])


@pytest.mark.parametrize("exercise_id", REAL)
def test_starter_fails(exercise_id):
    result = grade(exercise_id, read(exercise_id, "starter.py"))
    assert result["error"] is None and not result["passed"] and failed(result)


@pytest.mark.parametrize("exercise_id,code,expected", WRONG, ids=[f"{w[0]}#{k}" for k, w in enumerate(WRONG)])
def test_wrong_solution_fails_with_message(exercise_id, code, expected):
    result = grade(exercise_id, code)
    assert not result["passed"]
    assert any(expected in t["message"] for t in failed(result)), [t["message"] for t in failed(result)]


def test_wrong_solutions_cover_every_exercise():
    assert {w[0] for w in WRONG} == set(REAL)


def test_hidden_failure_does_not_reveal_its_data():
    result = grade("p1-quickstart/ghz", GHZ_WITHOUT_CHAIN)
    hidden = [t for t in failed(result) if not t["visible"]]
    assert hidden and all(t["name"].startswith("caso oculto") for t in hidden)
    for t in hidden:
        assert "5" not in t["message"] and "7" not in t["message"], t


def test_run_mode_returns_output_without_tests():
    result = grade("p1-quickstart/ghz", "print('hola')", mode="run")
    assert result["stdout"] == "hola\n" and result["tests"] == [] and result["error"] is None and result["passed"]


def test_missing_name_is_explained():
    result = grade("p1-quickstart/ghz", "x = 1")
    assert not result["passed"]
    assert all("Falta definir `ghz`" in t["message"] for t in result["tests"])


def test_syntax_error_names_the_line():
    result = grade("p1-quickstart/ghz", "x = 1\ndef f(:\n")
    assert result["error"].startswith("SyntaxError") and "línea 2" in result["error"] and result["tests"] == []


def test_runtime_error_names_the_learner_line():
    result = grade("p1-quickstart/ghz", "x = 1\nprint(y)\n")
    assert result["error"] == "NameError: name 'y' is not defined (línea 2: print(y))"


def test_failure_inside_a_case_is_reported_as_the_learner_code():
    result = grade("p1-quickstart/ghz", "def ghz(n):\n    raise ValueError('no sé')\n")
    assert any("Tu código lanzó ValueError: no sé" in t["message"] for t in failed(result))


def test_infinite_loop_is_stopped():
    result = grade("p1-quickstart/ghz", "while True:\n    pass\n", timeout=2)
    assert result["error"] == "Tu código tardó más de 2 s y se detuvo." and not result["passed"]


def test_oversized_code_is_refused():
    result = grade("p1-quickstart/ghz", "x = 1\n" * 10_000)
    assert "supera" in result["error"] and not result["passed"]


def test_blocked_module_cannot_be_imported():
    result = grade("p1-quickstart/ghz", "import qiskit_aer", mode="run", block=("qiskit_aer",))
    assert result["error"].startswith("ModuleNotFoundError: import of qiskit_aer halted")


def test_unknown_or_malformed_id_is_rejected():
    with pytest.raises(ValueError):
        grade("p1-quickstart/no-existe", "")
    with pytest.raises(ValueError):
        grade("../etc/passwd", "")


SECRET_SOLUTION = "SECRETO_SOLUCION"
SECRET_HIDDEN = "SECRETO_CASO_OCULTO"


def write_exercise(base, eid, *, solution="x = 1\n", starter="x = 0\n", check=None):
    d = base / eid
    d.mkdir(parents=True)
    (d / "solution.py").write_text(solution, encoding="utf-8")
    (d / "starter.py").write_text(starter, encoding="utf-8")
    check = check or (
        "from qgcheck import learner, visible\n\n\n"
        "@visible('x vale uno')\n"
        "def test_shown():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
        f"def test_hidden():\n    assert learner.x == 1, '{SECRET_HIDDEN}'\n")
    (d / "check.py").write_text(check, encoding="utf-8")


def lesson_with(*blocks):
    return dict(id="leccion", beats=[dict(id="paso", scene=list(blocks))])


def exercise_block(eid):
    return dict(type="exercise", exercise=eid, prompt="Haz x.", level=2, needs="qiskit", hints=["pista"])


@pytest.fixture
def fixture_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("QG_EXERCISES", str(tmp_path))
    build.ERRORS.clear()
    yield tmp_path
    build.ERRORS.clear()


def test_build_publishes_only_public_fields(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno", solution=f"x = 1  # {SECRET_SOLUTION}\n")
    les = lesson_with(dict(type="box", kind="idea", title="t", body=[exercise_block("leccion/uno")]))
    build.publish_exercises(les, set())
    assert build.ERRORS == []
    published = json.dumps(les, ensure_ascii=False)
    assert SECRET_SOLUTION not in published and SECRET_HIDDEN not in published and "test_hidden" not in published
    blk = les["beats"][0]["scene"][0]["body"][0]
    assert blk["starter"] == "x = 0" and blk["cases"] == ["x vale uno"]
    assert blk["prompt"] == "Haz x." and blk["hints"] == ["pista"] and blk["level"] == 2 and blk["needs"] == "qiskit"
    assert set(blk) == {"type", "exercise", "prompt", "level", "needs", "hints", "starter", "cases"}


def test_build_rejects_a_broken_exercise_reference(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno")
    write_exercise(fixture_dir, "otra/dos")
    (fixture_dir / "leccion" / "uno" / "check.py").write_text("def test_only_hidden():\n    pass\n", encoding="utf-8")
    seen = set()
    for eid in ("leccion/uno", "leccion/uno", "otra/dos", "leccion/falta", "Leccion/Mal"):
        build.publish_exercises(lesson_with(exercise_block(eid)), seen)
    text = "\n".join(build.ERRORS)
    assert "leccion/uno no tiene ningún caso @visible" in text
    assert "otra/dos debe estar en exercises/leccion/" in text
    assert "leccion/falta no tiene starter.py, solution.py, check.py" in text
    assert "id de ejercicio inválido" in text
    assert "leccion/uno está repetido" in text


def test_exercise_rejects_unknown_level_and_needs():
    from lib import Exercise
    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=4)
    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=1, needs="gpu")


def test_tool_accepts_a_sound_exercise(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno")
    assert exercises_tool.problems("leccion/uno", "qiskit") == []


def test_tool_flags_a_failing_solution(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno", solution="x = 2\n")
    assert any("solution.py no pasa: x vale uno: x debería valer 1" in p for p in exercises_tool.problems("leccion/uno", "qiskit"))


def test_tool_flags_a_starter_that_is_already_solved(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1\n")
    assert "starter.py ya pasa todos los casos" in exercises_tool.problems("leccion/uno", "qiskit")


def test_tool_flags_a_starter_that_crashes(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1 / 0\n")
    assert any("starter.py falla al ejecutarse: ZeroDivisionError" in p for p in exercises_tool.problems("leccion/uno", "qiskit"))


def test_tool_flags_needs_that_does_not_match_the_solution(fixture_dir):
    write_exercise(fixture_dir, "leccion/uno", solution="import qiskit_aer\nx = 1\n")
    write_exercise(fixture_dir, "leccion/dos")
    assert any('needs="qiskit" pero solution.py necesita qiskit_aer' in p for p in exercises_tool.problems("leccion/uno", "qiskit"))
    assert exercises_tool.problems("leccion/uno", "aer") == []
    assert 'needs="aer" pero solution.py pasa sin qiskit_aer' in exercises_tool.problems("leccion/dos", "aer")


def test_tool_reports_a_malformed_declared_id(monkeypatch, capsys):
    monkeypatch.setattr(exercises_tool, "declared", lambda: {"Mal/ID": "qiskit"})
    monkeypatch.setattr(sys, "argv", ["exercises.py"])
    with pytest.raises(SystemExit) as stop:
        exercises_tool.main()
    assert stop.value.code == 1
    assert "id de ejercicio inválido" in capsys.readouterr().out


def load_serve():
    tool = importlib.util.spec_from_file_location("serve_tool", ROOT / "tools" / "serve.py")
    module = importlib.util.module_from_spec(tool)
    tool.loader.exec_module(module)
    return module


@pytest.fixture
def server():
    import threading
    from functools import partial
    from http.server import ThreadingHTTPServer

    serve = load_serve()
    handler = type("Quiet", (serve.Handler,), {"log_message": lambda *a: None})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def post(base, body, content_type="application/json", host=None):
    import urllib.error
    import urllib.request

    req = urllib.request.Request(base + "/run", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": content_type, **({"Host": host} if host else {})})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


def test_server_grades_the_solution_and_a_wrong_answer(server):
    solution = (ROOT / "exercises" / "p1-quickstart" / "ghz" / "solution.py").read_text(encoding="utf-8")
    status, ok = post(server, {"exercise": "p1-quickstart/ghz", "code": solution, "mode": "check"})
    assert (status, ok["passed"]) == (200, True)
    status, bad = post(server, {"exercise": "p1-quickstart/ghz", "code": "def ghz(n):\n    return 1\n"})
    assert status == 200 and not bad["passed"]


def test_server_serves_the_site_and_rejects_bad_requests(server):
    import urllib.request

    assert b"<title>" in urllib.request.urlopen(server + "/index.html").read()
    assert post(server, {"exercise": "../x", "code": ""})[0] == 400
    assert post(server, {"exercise": "p1-quickstart/ghz", "code": ""}, content_type="text/plain")[0] == 403
    assert post(server, {"exercise": "p1-quickstart/ghz", "code": ""}, host="evil.example")[0] == 403
