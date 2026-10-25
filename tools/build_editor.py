from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="qg-editor-") as directory:
        output = Path(directory) / "editor.js"
        executable = "esbuild.exe" if os.name == "nt" else "esbuild"
        esbuild = ROOT / "editor" / "node_modules" / ".bin" / executable
        subprocess.run(
            [
                str(esbuild),
                "src/index.js",
                "--bundle",
                "--minify",
                "--format=iife",
                "--target=es2020",
                f"--outfile={output}",
                "--log-level=warning",
            ],
            cwd=ROOT / "editor",
            check=True,
        )
        if output.read_bytes() != (ROOT / "site/editor.js").read_bytes():
            raise SystemExit("site/editor.js no coincide con el bundle generado desde editor/src.")
    print("site/editor.js coincide con editor/src.")


if __name__ == "__main__":
    main()
