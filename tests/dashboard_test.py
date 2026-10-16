"""Prueba tools/dashboard.py contra una base D1 local con el esquema del Worker y filas conocidas.

    uv run pytest tests/dashboard_test.py

Necesita `bun install` en runner/worker, que trae wrangler; sin él, se omite.
"""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "runner" / "worker"
TOOL = ROOT / "tools" / "dashboard.py"

pytestmark = pytest.mark.skipif(
    not shutil.which("bunx") or not (WORKER / "node_modules" / ".bin" / "wrangler").exists(),
    reason="falta bun o wrangler: ejecuta `bun install` en runner/worker",
)


def at(day, hour=12):
    """Segundos Unix de un día de octubre de 2026 a una hora UTC."""
    moment = datetime.datetime(2026, 10, day, hour, tzinfo=datetime.timezone.utc)
    return int(moment.timestamp())


def epoch_day(day):
    return at(day, 0) // 86400


def attempt(day, user, exercise, mode, outcome, failed=(), hints=0):
    failed = json.dumps(list(failed)).replace("'", "''")
    who = f"'{user}'" if user else "NULL"
    return (
        "INSERT INTO attempts (at, user_id, exercise, mode, outcome, failed, hints, ms, code_bytes) "
        f"VALUES ({at(day)}, {who}, '{exercise}', '{mode}', '{outcome}', '{failed}', {hints}, 10, 100)"
    )


def state(user, exercise, hints, passed, day):
    return (
        "INSERT INTO exercise_state (user_id, exercise, hints, checks, passed, updated_at) "
        f"VALUES ('{user}', '{exercise}', {hints}, 1, {passed}, {at(day) * 1000})"
    )


# Periodo de la prueba: del 5 al 11 de octubre, ambos incluidos.
SEED = [
    "INSERT INTO users (id, created_day, seen_day) VALUES "
    f"('u1', {epoch_day(5)}, {epoch_day(9)}), ('u2', {epoch_day(11)}, {epoch_day(11)}), "
    f"('u3', {epoch_day(4)}, {epoch_day(9)}), ('u4', {epoch_day(12)}, {epoch_day(12)})",
    # Dentro del periodo: p1/ghz falla 4 veces (u1 dos, u2 una, una anónima), con los casos
    # «chain» (3), «measure» (2) y «size» (1); p1/bell falla una vez por error y una por timeout.
    attempt(6, "u1", "p1/ghz", "check", "fail", ["chain", "measure"]),
    attempt(7, "u1", "p1/ghz", "check", "fail", ["chain"]),
    attempt(8, "u2", "p1/ghz", "check", "fail", ["size", "measure"]),
    attempt(9, None, "p1/ghz", "check", "fail", ["chain"]),
    attempt(9, "u1", "p1/ghz", "check", "pass"),
    attempt(10, None, "p1/bell", "check", "error"),
    attempt(10, "u2", "p1/bell", "check", "timeout"),
    # No son comprobaciones fallidas: una ejecución sin comprobar y una que pasa.
    attempt(10, "u1", "p1/ghz", "run", "fail", ["chain"]),
    attempt(10, None, "p1/bell", "check", "pass"),
    # Fuera del periodo.
    attempt(4, "u3", "p1/ghz", "check", "fail", ["chain"]),
    attempt(12, "u4", "p1/ghz", "check", "fail", ["chain"]),
    "INSERT INTO lesson_done (user_id, lesson, done_at) VALUES "
    f"('u1', 'p1', {at(7)}), ('u2', 'p1', {at(9)}), ('u1', 'p2', {at(8)}), "
    f"('u3', 'p1', {at(4)}), ('u4', 'p3', {at(12)})",
    # Alumnos que aprobaron: u1 y u2 abrieron pistas en p1/ghz, u1 ninguna en p1/bell.
    state("u1", "p1/ghz", 3, 1, 9),
    state("u2", "p1/ghz", 2, 1, 10),
    state("u1", "p1/bell", 0, 1, 9),
    state("u2", "p1/bell", 5, 0, 10),
    state("u3", "p1/ghz", 4, 1, 4),
]

PERIOD = ["--since", "2026-10-05", "--until", "2026-10-11"]

EXPECTED = {
    "period": {"since": "2026-10-05", "until": "2026-10-11"},
    "summary": {"new_users": 2, "active_users": 2, "attempts": 9, "anonymous_attempts": 3},
    "completions": [
        {"lesson": "p1", "completions": 2},
        {"lesson": "p2", "completions": 1},
    ],
    "failed_checks": [
        {"exercise": "p1/ghz", "failed_checks": 4, "users": 2, "anonymous": 1},
        {"exercise": "p1/bell", "failed_checks": 2, "users": 1, "anonymous": 1},
    ],
    "failed_cases": [
        {"exercise": "p1/ghz", "case": "chain", "failures": 3},
        {"exercise": "p1/ghz", "case": "measure", "failures": 2},
        {"exercise": "p1/ghz", "case": "size", "failures": 1},
    ],
    "hints_before_pass": [
        {"exercise": "p1/ghz", "passed_by": 2, "hints": 5, "hints_per_learner": 2.5},
    ],
}

TEXT = """\
Periodo: 2026-10-05 a 2026-10-11 (UTC)

Usuarios nuevos        2
Usuarios con intentos  2
Intentos               9
Intentos sin cuenta    3

Lecciones terminadas
lección  terminadas
p1                2
p2                1

Ejercicios con más comprobaciones fallidas
ejercicio  fallidas  con cuenta  anónimas
p1/ghz            4           2         1
p1/bell           2           1         1

Casos que más fallan
ejercicio  caso     fallos
p1/ghz     chain         3
p1/ghz     measure       2
p1/ghz     size          1

Ejercicios aprobados con más pistas abiertas
ejercicio  aprobaron  pistas  por alumno
p1/ghz             2       5         2.5"""


def wrangler(persist, *args):
    config = persist / "wrangler.json"
    config.write_text(
        json.dumps(
            {
                "name": "qg-dashboard-test",
                "compatibility_date": "2026-10-01",
                "d1_databases": [
                    {"binding": "DB", "database_name": "test", "database_id": "0" * 8 + "-0000-0000-0000-" + "0" * 12}
                ],
            }
        )
    )
    cmd = ["bunx", "wrangler", "d1", "execute", "test", "--config", str(config), "--local"]
    cmd += ["--persist-to", str(persist / "state"), *args]
    done = subprocess.run(cmd, cwd=WORKER, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.fixture(scope="module")
def persist(tmp_path_factory):
    path = tmp_path_factory.mktemp("d1")
    wrangler(path, "--file", str(WORKER / "src" / "schema.sql"))
    seed = path / "seed.sql"
    seed.write_text(";\n".join(SEED) + ";\n")
    wrangler(path, "--file", str(seed))
    return path / "state"


def dashboard(persist, *args):
    cmd = [sys.executable, str(TOOL), "--local", "--persist-to", str(persist), "--database", "test"]
    done = subprocess.run([*cmd, *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def test_json_rows(persist):
    out = json.loads(dashboard(persist, "--json", *PERIOD))
    assert out == EXPECTED


def test_text_report(persist):
    assert dashboard(persist, *PERIOD).rstrip("\n") == TEXT


def test_limit_cuts_every_ranking(persist):
    out = json.loads(dashboard(persist, "--json", "--limit", "1", *PERIOD))
    assert out["failed_checks"] == EXPECTED["failed_checks"][:1]
    assert out["failed_cases"] == EXPECTED["failed_cases"][:1]
    assert out["completions"] == EXPECTED["completions"]


def test_empty_period_prints_zeros(persist):
    out = json.loads(dashboard(persist, "--json", "--since", "2026-09-01", "--until", "2026-09-02"))
    assert out["summary"] == {"new_users": 0, "active_users": 0, "attempts": 0, "anonymous_attempts": 0}
    assert out["completions"] == out["failed_checks"] == out["failed_cases"] == []
    assert out["hints_before_pass"] == []


def test_remote_needs_a_database_id():
    done = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True)
    assert done.returncode == 2
    assert "--database-id" in done.stderr
