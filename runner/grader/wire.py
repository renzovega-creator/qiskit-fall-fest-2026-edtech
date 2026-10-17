"""Formato de mensajes de datos entre el comprobador y el proceso del alumno.

Cada mensaje es JSON precedido por su longitud en 4 bytes. El canal admite
valores básicos, arrays numéricos y circuitos QPY, pero nunca deserializa código.
"""

import base64
import io
import json
import os
import re
import struct
import sys
from typing import Any

MESSAGE_CAP = 4 * 2**20
DTYPE = re.compile(r"[<>|=]?[biufc]\d{1,2}")
BROKEN = "Tu código terminó o rompió el canal antes de dar un resultado."


class WireError(Exception):
    """El otro extremo cerró el canal o envió algo que no es un mensaje válido."""


def encode(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, tuple):
        return {"$": "tuple", "v": [encode(v) for v in value]}
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError("un diccionario con claves que no son texto")
        return {"$": "dict", "v": {k: encode(v) for k, v in value.items()}}
    if isinstance(value, complex):
        return {"$": "complex", "v": [value.real, value.imag]}
    np = sys.modules.get("numpy")
    if np is not None:
        if isinstance(value, np.generic):
            return encode(value.item())
        if isinstance(value, np.ndarray) and value.dtype.kind in "biufc":
            return {"$": "array", "dtype": value.dtype.str, "v": encode(value.tolist())}
    if "qiskit" in sys.modules:
        from qiskit import QuantumCircuit, qpy

        if isinstance(value, QuantumCircuit):
            buffer = io.BytesIO()
            qpy.dump(value, buffer)
            return {"$": "circuit", "v": base64.b64encode(buffer.getvalue()).decode("ascii")}
    raise TypeError(f"un valor de tipo {type(value).__name__}")


def decode(obj: Any) -> Any:
    if isinstance(obj, list):
        return [decode(v) for v in obj]
    if not isinstance(obj, dict):
        return obj
    kind: Any = obj.get("$")
    v: Any = obj.get("v")
    if kind == "tuple":
        return tuple(decode(x) for x in v)
    if kind == "dict":
        return {k: decode(x) for k, x in v.items()}
    if kind == "complex":
        return complex(v[0], v[1])
    if kind == "array":
        import numpy as np

        dtype = obj["dtype"]
        if not DTYPE.fullmatch(dtype):
            raise WireError(f"dtype no admitido: {dtype!r}")
        return np.array(decode(v), dtype=dtype)
    if kind == "circuit":
        from qiskit import qpy

        return qpy.load(io.BytesIO(base64.b64decode(v, validate=True)))[0]
    raise WireError("un valor con un tipo desconocido")


def send(fd: int, message: dict[str, Any]) -> None:
    data = json.dumps(message).encode("utf-8")
    if len(data) > MESSAGE_CAP:
        raise WireError("mensaje demasiado grande")
    view = memoryview(struct.pack(">I", len(data)) + data)
    try:
        while view:
            view = view[os.write(fd, view) :]
    except OSError as e:
        raise WireError(f"no se pudo escribir: {e}") from e


def _read(fd: int, size: int) -> bytes:
    chunks: list[bytes] = []
    while size:
        try:
            chunk = os.read(fd, min(size, 65536))
        except OSError as e:
            raise WireError(f"no se pudo leer: {e}") from e
        if not chunk:
            raise WireError("el canal se cerró")
        chunks.append(chunk)
        size -= len(chunk)
    return b"".join(chunks)


def receive(fd: int) -> dict[str, Any]:
    (size,) = struct.unpack(">I", _read(fd, 4))
    if size > MESSAGE_CAP:
        raise WireError("mensaje demasiado grande")
    try:
        message = json.loads(_read(fd, size))
    except (ValueError, RecursionError) as e:
        raise WireError("el mensaje no es JSON") from e
    if not isinstance(message, dict):
        raise WireError("el mensaje no es un objeto")
    return message
