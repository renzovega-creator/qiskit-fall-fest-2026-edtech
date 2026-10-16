"""Servidor HTTP del corredor: POST /run y GET /health.

No depende del anfitrión: lo mismo corre en Cloudflare Containers que en Docker.
El contrato está en docs/runner.md y el ciclo de las ranuras en
docs/architecture.md. Si no queda una ranura libre, responde 503.
"""
import json
import os
import queue
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import sandbox

EXERCISES = Path(os.environ.get("QG_EXERCISES", "/app/exercises"))
PORT = int(os.environ.get("PORT", "8080"))
MAX_CODE_BYTES = 20_000
# Un carácter de control ocupa 6 bytes escapado en JSON; el resto es la envoltura.
MAX_BODY_BYTES = 6 * MAX_CODE_BYTES + 1024
EXERCISE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*")
LIMITS = sandbox.Limits(
    wall_s=float(os.environ.get("QG_WALL_S", "10")),
    mem_mb=int(os.environ.get("QG_MEM_MB", "512")),
    scratch_mb=int(os.environ.get("QG_SCRATCH_MB", "64")),
)
FREE_SLOTS = queue.Queue()
for _slot in range(int(os.environ.get("QG_JOBS", "1"))):
    FREE_SLOTS.put(_slot)
MESSAGE_CAP = 500


class BadRequest(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def parse_request(raw):
    try:
        body = json.loads(raw)
    except ValueError:
        raise BadRequest(400, "el cuerpo no es JSON")
    if not isinstance(body, dict):
        raise BadRequest(400, "el cuerpo debe ser un objeto")
    code, mode, exercise = body.get("code"), body.get("mode", "run"), body.get("exercise")
    if not isinstance(code, str):
        raise BadRequest(400, "`code` debe ser texto")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise BadRequest(413, f"el código supera {MAX_CODE_BYTES} bytes")
    if mode not in ("run", "check"):
        raise BadRequest(400, "`mode` es `run` o `check`")
    check = None
    if mode == "check":
        if not isinstance(exercise, str) or not EXERCISE_ID.fullmatch(exercise):
            raise BadRequest(400, "`exercise` debe ser `lección/ejercicio`")
        check = EXERCISES / exercise / "check.py"
        if not check.is_file():
            raise BadRequest(404, f"no existe el ejercicio {exercise}")
    return code, mode, check


def parse_report(raw):
    """Valida lo que escribió el plugin; el hijo lo controla el alumno."""
    try:
        items = json.loads(raw)["tests"]
    except (ValueError, KeyError, TypeError):
        return []
    tests = []
    for t in items if isinstance(items, list) else []:
        if not isinstance(t, dict):
            continue
        name, message = t.get("name"), t.get("message")
        tests.append({
            "name": name[:MESSAGE_CAP] if isinstance(name, str) else None,
            "visible": t.get("visible") is True,
            "passed": t.get("passed") is True,
            "message": message[:MESSAGE_CAP] if isinstance(message, str) else None,
        })
    return tests


def execute(slot, code, mode, check):
    files = {"main.py": code}
    if mode == "run":
        argv = [sys.executable, "-u", "{dir}/main.py"]
        out = sandbox.run_job(slot, files, argv, LIMITS, {})
    else:
        argv = [
            sys.executable, "-u", "-P", "-m", "pytest", "-c", str(sandbox.APP / "pytest.ini"),
            "-p", "qgcheck.plugin", str(check),
        ]
        out = sandbox.run_job(
            slot, files, argv, LIMITS, {"QG_LEARNER": "{dir}/main.py"}, report=True,
        )
    tests = parse_report(out.report) if mode == "check" else []
    clean = out.exit_code == 0 and not out.timed_out and out.killed is None
    ok = clean if mode == "run" else clean and bool(tests) and all(t["passed"] for t in tests)
    return {
        "ok": ok,
        "stdout": out.stdout,
        "stderr": out.stderr,
        "exit_code": out.exit_code,
        "timed_out": out.timed_out,
        "killed": out.killed,
        "tests": tests,
        "ms": out.ms,
        "peak_mb": out.peak_mb,
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def reply(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, {"ok": True})
        else:
            self.reply(404, {"error": "no existe"})

    def do_POST(self):
        if self.path != "/run":
            self.reply(404, {"error": "no existe"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = -1
        if not 0 <= length <= MAX_BODY_BYTES:
            self.close_connection = True
            self.reply(413 if length > 0 else 400, {"error": "cuerpo ausente o demasiado grande"})
            return
        try:
            code, mode, check = parse_request(self.rfile.read(length))
        except BadRequest as e:
            self.reply(e.status, {"error": str(e)})
            return
        try:
            slot = FREE_SLOTS.get_nowait()
        except queue.Empty:
            self.reply(503, {"error": "ocupado"})
            return
        try:
            self.reply(200, execute(slot, code, mode, check))
        finally:
            FREE_SLOTS.put(slot)


def main():
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
