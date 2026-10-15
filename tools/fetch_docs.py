"""Descarga las guías originales de Qiskit/documentation en .cache/qiskit-docs.

    python tools/fetch_docs.py

Trae solo docs/guides en la versión fijada en tools/qiskit-docs.commit.
Si .cache/qiskit-docs ya está en esa versión no hace nada.
build.py y extract.py leen de aquí. Para actualizar las guías, cambia el hash de
tools/qiskit-docs.commit y ejecuta de nuevo.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / ".cache" / "qiskit-docs"
PIN = Path(__file__).resolve().parent / "qiskit-docs.commit"
REPO = "https://github.com/Qiskit/documentation.git"


def git(*args, capture=False):
    return subprocess.run(["git", "-C", str(DEST), *args], check=True, text=True,
                          capture_output=capture).stdout


def current():
    try:
        return git("rev-parse", "HEAD", capture=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main():
    commit = PIN.read_text(encoding="utf-8").strip()
    if current() == commit and (DEST / "docs" / "guides" / "_toc.json").exists():
        print(f"guías al día: {commit[:8]}")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    if not (DEST / ".git").exists():
        git("init", "--quiet")
        git("remote", "add", "origin", REPO)
    git("sparse-checkout", "set", "docs/guides")
    git("fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", commit)
    git("checkout", "--quiet", "--force", commit)
    print(f"guías descargadas: {commit[:8]} en {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
