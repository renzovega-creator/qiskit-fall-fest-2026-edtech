"""Servidor HTTP del corredor: POST /run y GET /health.

No depende del anfitrión: lo mismo corre en Cloudflare Containers que en Docker.
El contrato está en docs/runner.md y el ciclo de las ranuras en
docs/architecture.md. Si no queda una ranura libre, responde 503.
"""

import json
import os
import queue
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import sandbox

from qgcheck import spec
from qgcheck.runner import MAX_CODE

PORT = int(os.environ.get("PORT", "8080"))
# Un carácter de control ocupa 6 bytes escapado en JSON; el resto es la envoltura.
MAX_BODY_BYTES = 6 * MAX_CODE + 1024
NOT_FINISHED = "El código no terminó: se quedó sin memoria o el proceso se cerró."
LIMITS = sandbox.Limits(
    wall_s=float(os.environ.get("QG_WALL_S", "10")),
    mem_mb=int(os.environ.get("QG_MEM_MB", "512")),
    scratch_mb=int(os.environ.get("QG_SCRATCH_MB", "64")),
)
FREE_SLOTS: queue.Queue[int] = queue.Queue()
for _slot in range(int(os.environ.get("QG_JOBS", "1"))):
    FREE_SLOTS.put(_slot)
MESSAGE_CAP = 500


class BadRequest(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def parse_request(raw: bytes) -> tuple[str, str, Path | None]:
    try:
        body = json.loads(raw)
    except ValueError:
        raise BadRequest(400, "el cuerpo no es JSON") from None
    if not isinstance(body, dict):
        raise BadRequest(400, "el cuerpo debe ser un objeto")
    code, mode, exercise = body.get("code"), body.get("mode", "run"), body.get("exercise")
    if not isinstance(code, str):
        raise BadRequest(400, "`code` debe ser texto")
    if len(code.encode("utf-8")) > MAX_CODE:
        raise BadRequest(413, f"el código supera {MAX_CODE} bytes")
    if mode not in ("run", "check"):
        raise BadRequest(400, "`mode` es `run` o `check`")
    check: Path | None = None
    if mode == "check":
        if not isinstance(exercise, str):
            raise BadRequest(400, "`exercise` debe ser `lección/ejercicio`")
        try:
            check = spec.folder(exercise) / "check.py"
        except ValueError:
            raise BadRequest(400, "`exercise` debe ser `lección/ejercicio`") from None
        if not check.is_file():
            raise BadRequest(404, f"no existe el ejercicio {exercise}")
    return code, mode, check


def parse_report(raw: bytes) -> tuple[str | None, list[dict[str, Any]]] | None:
    """Valida lo que escribió el trabajo; en `run` lo controla el alumno.

    Devuelve (error, casos), o None si no hay un informe válido.
    """
    try:
        report = json.loads(raw)
        error, items = report["error"], report["tests"]
    except (ValueError, KeyError, TypeError):
        return None
    if not (error is None or isinstance(error, str)) or not isinstance(items, list):
        return None
    tests: list[dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        name, message, hint = t.get("name"), t.get("message"), t.get("hint")
        tests.append(
            {
                "name": name[:MESSAGE_CAP] if isinstance(name, str) else None,
                "visible": t.get("visible") is True,
                "passed": t.get("passed") is True,
                "message": message[:MESSAGE_CAP] if isinstance(message, str) else None,
                "hint": hint if type(hint) is int and hint >= 1 else None,
            }
        )
    return error and error[:MESSAGE_CAP], tests


def stopped(killed: str) -> str:
    return {
        "time": f"Tu código tardó más de {LIMITS.wall_s:g} s y se detuvo.",
        "memory": f"Tu código usó más de {LIMITS.mem_mb} MB de memoria y se detuvo.",
        "disk": f"Tu código escribió más de {LIMITS.scratch_mb} MB y se detuvo.",
        "output": f"Tu código imprimió más de {LIMITS.out_bytes // 1024} KiB y se detuvo.",
    }[killed]


def execute(slot: int, code: str, mode: str, check: Path | None) -> dict[str, Any]:
    argv = [sys.executable, "-u", "-P", "-m", "grader.job", mode, "{dir}/main.py"]
    if check:
        argv.append(str(check))
    out = sandbox.run_job(slot, {"main.py": code}, argv, LIMITS, {}, report=True)
    report = parse_report(out.report)
    error: str | None
    tests: list[dict[str, Any]]
    if out.killed:
        error, tests = stopped(out.killed), []
    elif report is None:
        error, tests = NOT_FINISHED, []
    else:
        error, tests = report
    if mode == "run":
        tests = []
    return {
        "passed": error is None
        and (mode == "run" or (bool(tests) and all(t["passed"] for t in tests))),
        "stdout": out.output,
        "error": error,
        "tests": tests,
        "ms": out.ms,
        "killed": out.killed,
        "peak_mb": out.peak_mb,
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def reply(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.reply(200, {"ok": True})
        else:
            self.reply(404, {"error": "no existe"})

    def do_POST(self) -> None:
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


def main() -> None:
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
