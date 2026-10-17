"""Convierte las guías (.mdx / .ipynb) de .cache/qiskit-docs/docs/guides en texto legible en
.cache/qiskit-docs/text/<nombre>.md.

    python tools/fetch_docs.py && uv run python tools/extract.py
Las celdas de código van entre ```python y sus salidas de texto entre ```salida (las imágenes se omiten).
"""

import json
from pathlib import Path
from typing import Any

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "qiskit-docs"
SRC, OUT = CACHE / "docs" / "guides", CACHE / "text"


def notebook_text(f: Path) -> str:
    parts: list[Any] = []
    for c in json.loads(f.read_text(encoding="utf-8"))["cells"]:
        src = "".join(c["source"])
        if c["cell_type"] == "markdown":
            parts.append(src)
        elif c["cell_type"] == "code":
            parts.append(f"```python\n{src}\n```")
            for o in c.get("outputs", []):
                t = o.get("text") or o.get("data", {}).get("text/plain")
                if t:
                    parts.append("```salida\n" + "".join(t)[:1500] + "\n```")
                elif "image/png" in o.get("data", {}):
                    parts.append("[imagen]")
    return "\n\n".join(parts)


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"falta {SRC}: ejecuta python tools/fetch_docs.py")
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.iterdir()):
        if f.suffix == ".mdx":
            txt = f.read_text(encoding="utf-8")
        elif f.suffix == ".ipynb":
            txt = notebook_text(f)
        else:
            continue
        (OUT / f"{f.stem}.md").write_text(txt, encoding="utf-8")
    print(len(list(OUT.iterdir())), "páginas")


if __name__ == "__main__":
    main()
