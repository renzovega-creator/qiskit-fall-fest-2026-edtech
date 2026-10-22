"""Localiza un ejercicio en exercises/ y lee de check.py los casos y lo que build.py publica.

exercises/<lección>/<ejercicio>/ guarda starter.py (lo que ve el alumno), solution.py (la
referencia) y check.py (los casos). Solo starter.py y los nombres de los casos visibles llegan
a site/.
"""

import importlib.util
import os
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FILES = ("starter.py", "solution.py", "check.py")
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*")


def exercises_dir() -> Path:
    return Path(os.environ.get("QG_EXERCISES") or ROOT / "exercises")


def folder(exercise_id: str) -> Path:
    """Devuelve la carpeta y rechaza ids que no sigan el formato publicado."""
    if not ID.fullmatch(exercise_id):
        raise ValueError(f"id de ejercicio inválido: {exercise_id!r}")
    return exercises_dir() / exercise_id


def all_ids() -> list[str]:
    """Devuelve ordenados los ids de las carpetas de ejercicio."""
    base = exercises_dir()
    return sorted(d.relative_to(base).as_posix() for d in base.glob("*/*") if d.is_dir())


def missing_files(exercise_id: str) -> list[str]:
    d = folder(exercise_id)
    return [f for f in FILES if not (d / f).is_file()]


def load_module(check_path: Path) -> ModuleType:
    """Importa check.py, que no debe leer `learner` ni correr código del alumno al importarse."""
    spec = importlib.util.spec_from_file_location("check", check_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cases(check_path: Path) -> list[tuple[Callable[..., Any], str | None]]:
    """[(función, nombre visible o None)] de cada test_* de check.py, en el orden en que se definen."""
    module = load_module(check_path)
    return [
        (fn, getattr(fn, "qg_visible", None))
        for name, fn in vars(module).items()
        if name.startswith("test_") and callable(fn)
    ]


def public(exercise_id: str) -> dict[str, Any]:
    """Devuelve el código inicial y los nombres de los casos visibles."""
    d = folder(exercise_id)
    return dict(
        starter=(d / "starter.py").read_text(encoding="utf-8").rstrip("\n"),
        cases=[name for _, name in load_cases(d / "check.py") if name],
    )
