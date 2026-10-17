from typing import Any

from . import qpy as qpy

class QuantumCircuit:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
