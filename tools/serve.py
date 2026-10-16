"""Sirve site/ y corrige los ejercicios de código en el equipo.

    uv run python tools/serve.py [puerto]

Es `python -m http.server` más `POST /run`, que el editor de los ejercicios llama con
{"exercise": id, "code": texto, "mode": "run"|"check"} y recibe el resultado de qgcheck.grade.
Escucha solo en 127.0.0.1 y ejecuta el código en un proceso de tu usuario, sin más aislamiento:
sirve para practicar en tu equipo, no para exponerlo en red.
"""
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qgcheck import grade  # noqa: E402
from qgcheck.runner import MAX_CODE  # noqa: E402

PORT = 8810


class Handler(SimpleHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/run":
            return self.reply(404, {"error": "No existe."})
        # Otra web podría enviar el POST desde el navegador del alumno: application/json obliga a una
        # petición previa que este servidor no responde, y Host evita el rebinding de DNS.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host not in ("localhost", "127.0.0.1") or self.headers.get("Content-Type") != "application/json":
            return self.reply(403, {"error": "Petición no permitida."})
        size = int(self.headers.get("Content-Length") or 0)
        if size > 2 * MAX_CODE:
            return self.reply(413, {"error": "El código es demasiado largo."})
        try:
            req = json.loads(self.rfile.read(size))
            result = grade(req["exercise"], req["code"], req.get("mode", "check"))
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": f"Petición inválida: {exc}"})
        self.reply(200, result)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT / "site")))
    print(f"Curso en http://localhost:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
