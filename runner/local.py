"""Construye y ejecuta la imagen del corredor con Docker, con las banderas de aislamiento.

    python runner/local.py build
    python runner/local.py serve [--runtime runc|runsc]

`serve` construye la imagen si falta, imprime la URL del contenedor y lo deja
corriendo hasta Ctrl-C. El contenedor va en una red interna de Docker, sin salida
a internet, y se alcanza por su IP; eso funciona en Linux.

`QG_DOCKER` cambia el comando de Docker (por ejemplo `sudo docker`). `build` lee las
versiones de Python y de uv de mise.toml con `mise current`.
"""

import argparse
import json
import os
import shlex
import subprocess
import time
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "qg-runner"
INTERNAL_NET = "qg-runner-internal"
PORT = 8080
CAPS = ("SETUID", "SETGID", "KILL", "CHOWN", "FOWNER", "DAC_OVERRIDE")


def docker(*args: str, check: bool = True, capture: bool = True) -> str:
    cmd = [*shlex.split(os.environ.get("QG_DOCKER", "docker")), *args]
    proc = subprocess.run(cmd, check=check, text=True, capture_output=capture)
    return proc.stdout.strip() if capture else ""


def default_runtime() -> str:
    runtimes = json.loads(docker("info", "--format", "{{json .Runtimes}}"))
    return os.environ.get("QG_RUNTIME") or ("runsc" if "runsc" in runtimes else "runc")


def mise_version(tool: str) -> str:
    """La versión que mise.toml fija para `tool`."""
    proc = subprocess.run(["mise", "current", tool], check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def build(image: str = IMAGE) -> None:
    docker(
        "build",
        "-f",
        str(ROOT / "runner" / "Dockerfile"),
        "--build-arg",
        f"PYTHON_VERSION={mise_version('python')}",
        "--build-arg",
        f"UV_VERSION={mise_version('uv')}",
        "-t",
        image,
        str(ROOT),
        capture=False,
    )


def ensure_image(image: str = IMAGE) -> None:
    """Construye la imagen si Docker no la tiene."""
    if not docker("image", "inspect", "--format", "{{.Id}}", image, check=False):
        build(image)


@dataclass
class Container:
    name: str
    url: str
    runtime: str

    def stop(self) -> None:
        docker("rm", "-f", self.name, check=False)

    def exec(self, *argv: str) -> str:
        """Ejecuta un comando dentro del contenedor, como root."""
        return docker("exec", self.name, *argv)


def start(image: str = IMAGE, runtime: str | None = None, egress: bool = False) -> Container:
    """Arranca el contenedor, construyendo antes la imagen si falta, y espera a /health.

    Con `egress=True` usa la red por defecto de Docker, que sí sale a internet.
    Sirve para comprobar que el alumno no sale aunque la red lo permita.
    """
    ensure_image(image)
    runtime = runtime or default_runtime()
    if egress:
        network = "bridge"
    else:
        network = INTERNAL_NET
        if docker("network", "ls", "-q", "--filter", f"name=^{INTERNAL_NET}$") == "":
            docker("network", "create", "--internal", INTERNAL_NET)
    name = f"qg-runner-{uuid.uuid4().hex[:8]}"
    caps = [a for c in CAPS for a in ("--cap-add", c)]
    docker(
        "run",
        "-d",
        "--rm",
        "--name",
        name,
        "--runtime",
        runtime,
        "--network",
        network,
        "--read-only",
        "--ipc",
        "none",
        "--tmpfs",
        "/scratch:size=96m,mode=0755",
        "--tmpfs",
        "/tmp:size=4m,mode=0755",
        "--memory",
        "1g",
        "--cpus",
        "1",
        "--pids-limit",
        "256",
        "--cap-drop",
        "ALL",
        *caps,
        "--security-opt",
        "no-new-privileges",
        image,
    )
    container = Container(name, "", runtime)
    try:
        ip = docker(
            "inspect", "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", name
        )
        container.url = f"http://{ip}:{PORT}"
        wait_healthy(container.url)
    except BaseException:
        container.stop()
        raise
    return container


def wait_healthy(url: str, timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.02)
    raise TimeoutError(f"{url}/health no responde tras {timeout} s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("build", "serve"))
    parser.add_argument("--runtime", choices=("runc", "runsc"))
    args = parser.parse_args()
    if args.action == "build":
        build()
        return
    container = start(runtime=args.runtime)
    print(
        f"{container.url}  (runtime {container.runtime}, contenedor {container.name})", flush=True
    )
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        container.stop()


if __name__ == "__main__":
    main()
