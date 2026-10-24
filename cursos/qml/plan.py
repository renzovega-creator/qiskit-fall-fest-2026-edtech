"""Mapa del curso «Del ML al QML»: cada lección es un par concepto clásico ↔ equivalente cuántico.

Se construye con QG_CURSO=qml python lessons_src/build.py. Las lecciones no cubren guías de IBM,
así que la lista de guías de cada una va vacía.
"""

from typing import Any

PARTS: list[dict[str, Any]] = [
    dict(
        n=1,
        title="Nivel 1 · Probabilidad y muestreo",
        desc="La regla de Born es una distribución de probabilidad y cada shot es una muestra de Monte Carlo.",
        lessons=[("q1-montecarlo", "Monte Carlo ↔ shots", [])],
    ),
    dict(
        n=2,
        title="Nivel 2 · Kernels",
        desc="Una SVM solo necesita similitudes entre puntos: un circuito puede calcularlas en el espacio de Hilbert.",
        lessons=[("q2-kernel", "SVM con kernel RBF ↔ kernel cuántico", [])],
    ),
]
