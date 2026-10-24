# Del ML al QML

Curso en español que empareja cada concepto de estadística o machine learning con su equivalente
cuántico en Qiskit. Usa el motor de lecciones de este repositorio: `QG_CURSO=qml` hace que
`lessons_src/build.py` y `qgcheck` lean el plan, las lecciones y los ejercicios de esta carpeta.

| Nivel | Par | Ejercicio |
| --- | --- | --- |
| 1 | Monte Carlo ↔ shots (regla de Born, error $1/\sqrt N$) | `q1-montecarlo/estimar-p` |
| 2 | SVM con kernel RBF ↔ kernel cuántico (`QSVC`) | `q2-kernel/kernel-fidelidad` |
| 3 | Descenso de gradiente ↔ parameter-shift (próximamente) | — |

La portada (`site/index.html`) tiene tres ganchos diarios: el **reto del día** (predices un número
y Qiskit lo mide con `POST /run`, con la misma semilla para todos en una fecha), el **repaso
espaciado** (1, 3, 7 y 21 días) y el **nivel**.

## Correr

```sh
uv sync --python 3.15
uv pip install --python .venv/bin/python qiskit-machine-learning==0.9.1 scikit-learn edge-tts mutagen
QG_CURSO=qml .venv/bin/python lessons_src/build.py
QG_CURSO=qml .venv/bin/python tools/serve.py
```

Abre <http://localhost:8810/>. La narración se regenera con
`.venv/bin/python tools/tts.py site/lessons/<id>` (necesita red; sin ffmpeg usa mutagen).
`QG_CURSO=qml .venv/bin/python tools/exercises.py` comprueba que cada solución pasa y cada código
inicial falla.

`numeros.py` recalcula las cifras que muestran las lecciones.

## Créditos

Motor: [qiskit-guides](https://github.com/PedroRojasF/qiskit-guides-compartido). Inspiración
temática: el taller *An introduction to QML with PennyLane and PyTorch* de Jacob Cybulski
(2026); no se reutiliza su código ni sus slides.
