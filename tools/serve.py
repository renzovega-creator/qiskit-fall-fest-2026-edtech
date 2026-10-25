"""Sirve site/ y corrige los ejercicios de código en el equipo.

    uv run python tools/serve.py [puerto]

Es `python -m http.server` más `POST /run`, que el editor de los ejercicios llama con
{"exercise": id, "code": texto, "mode": "run"|"check"} y recibe el resultado de qgcheck.grade.
Escucha solo en 127.0.0.1 y ejecuta el código en un proceso de tu usuario, sin más aislamiento:
sirve para practicar en tu equipo, no para exponerlo en red.

qgcheck necesita fork, que Windows no tiene. Allí "run" ejecuta el código con el mismo Python, con
el límite de tiempo y de salida de qgcheck, y "check" responde que la corrección necesita Linux o
macOS.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qgcheck import grade, spec  # noqa: E402
from qgcheck.runner import MAX_CODE, OUT_BYTES, TIMEOUT  # noqa: E402

PORT = 8810
NO_CHECK = "Corregir ejercicios necesita Linux o macOS: qgcheck usa fork. En Windows, usa WSL."


def run_plain(exercise_id: str, code: str) -> dict[str, Any]:
    """Ejecuta el código sin qgcheck y devuelve un resultado con la forma de grade(mode="run")."""
    if not spec.folder(exercise_id).is_dir():
        raise ValueError(f"ejercicio desconocido: {exercise_id!r}")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="qg-") as work:
        main = Path(work) / "main.py"
        main.write_text(code, encoding="utf-8")
        env = os.environ | {"PYTHONIOENCODING": "utf-8", "MPLCONFIGDIR": work}
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(main)],
                cwd=work,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return dict(
                passed=False,
                stdout="",
                error=f"El código no terminó en {TIMEOUT} s.",
                tests=[],
                ms=round((time.monotonic() - start) * 1000),
                killed="time",
            )
    out = proc.stdout[:OUT_BYTES].decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
    return dict(
        passed=False,
        stdout=out,
        error=(err[-1] if err else f"El proceso terminó con código {proc.returncode}.")
        if proc.returncode
        else None,
        tests=[],
        ms=round((time.monotonic() - start) * 1000),
        killed="output" if len(proc.stdout) > OUT_BYTES else None,
    )


class Handler(SimpleHTTPRequestHandler):
    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code != 404:
            return super().send_error(code, message, explain)
        data = (ROOT / "site" / "404.html").read_bytes()
        self.send_response(code, message)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def reply(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/run":
            return self.reply(404, {"error": "No existe."})
        # Otra web podría enviar el POST desde el navegador del alumno: application/json obliga a una
        # petición previa que este servidor no responde, y Host evita el rebinding de DNS.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if (
            host not in ("localhost", "127.0.0.1")
            or self.headers.get("Content-Type") != "application/json"
        ):
            return self.reply(403, {"error": "Petición no permitida."})
        size = int(self.headers.get("Content-Length") or 0)
        if size > 2 * MAX_CODE:
            return self.reply(413, {"error": "El código es demasiado largo."})
        try:
            req = json.loads(self.rfile.read(size))
            mode = req.get("mode", "check")
            if hasattr(os, "fork"):
                result = grade(req["exercise"], req["code"], mode)
            elif mode == "run":
                result = run_plain(req["exercise"], req["code"])
            elif mode == "check":
                result = dict(passed=False, stdout="", error=NO_CHECK, tests=[], ms=0, killed=None)
            else:
                raise ValueError(f"modo inválido: {mode!r}")
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": f"Petición inválida: {exc}"})
        self.reply(200, result)


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), partial(Handler, directory=str(ROOT / "site"))
    )
    print(f"Curso en http://localhost:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
