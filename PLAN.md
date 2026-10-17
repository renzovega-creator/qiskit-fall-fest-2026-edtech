# Plan: de lecciones para ver a lecciones para hacer

Decidido el 2026-10-07. Problema: las lecciones son sobre todo para consumir
(ver, escuchar, 1–2 preguntas de memoria). Objetivo: que cada lección lleve a
**actuar** y a **reflexionar**.

## 1. El nuevo ciclo de cada lección

| Momento         | Qué pasa                                                                                  | Cómo se implementa                                                 |
| --------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Predecir**    | Antes de ver un resultado, apuestas una respuesta (conteos, profundidad, valor esperado). | `ask` antes de la revelación, no después. Mínimo 1 por lección.    |
| **Ver**         | La animación narrada actual, algo más corta.                                              | Igual que hoy.                                                     |
| **Hacer**       | Una misión en el cuaderno marimo de la lección.                                           | Paso «Tu turno» con la misión y el comando para abrir el cuaderno. |
| **Reflexionar** | 1–2 preguntas abiertas: «explícalo con tus palabras», «¿qué pasaría si…?».                | Cuadro de texto guardado en el navegador; se ve al volver.         |
| **Resumir**     | El resumen actual.                                                                        | Igual que hoy.                                                     |

## 2. Cuadernos de práctica con marimo

- Un cuaderno por lección: `practica/<id>.py`, que se abre con
  `uv run marimo edit practica/<id>.py`.
- **¿Por qué marimo y no Jupyter?** Es reactivo: cambias algo y todo se
  recalcula, así que las comprobaciones dicen ✅ o ❌ al instante. Trae
  controles deslizantes, buenos para explorar parámetros. Sus archivos son `.py`
  normales: ligeros, fáciles de versionar y verificables con `tools/verify.py`.
- **La contra:** las guías de IBM y la comunidad usan Jupyter. Una misión de la
  Parte I enseña a convertir entre los dos formatos (`marimo convert`) para que
  también sepas usar Jupyter.
- Ejercicios en tres niveles: 🟢 reproducir · 🟡 modificar · 🔴 crear. Cada uno
  con su comprobación.
- Qiskit no corre en el navegador, así que los cuadernos se ejecutan en tu
  equipo, con el entorno uv del proyecto.

## 3. Proyecto que atraviesa el curso: la cadena de espines (Ising)

Un solo experimento que crece parte por parte (`practica/proyecto/`), con un
objetivo físico claro: ver cómo evoluciona la magnetización de una cadena de
espines tras un cambio brusco del campo.

| Parte | Hito del proyecto                                                                     |
| ----- | ------------------------------------------------------------------------------------- |
| I     | Crear la cuenta de IBM Quantum (plan Open). Un paso de Trotter con 2 espines.         |
| II    | Hamiltoniano como `SparsePauliOp`; circuito de N pasos; observables de magnetización. |
| III   | Transpilar para `FakeFez`; comparar niveles; profundidad frente a número de pasos.    |
| IV    | Magnetización en el tiempo: exacta frente a simulación con ruido (Aer).               |
| V     | **Primera ejecución en un QPU real** (presupuesto ≤ 1 min).                           |
| VI    | Mitigar: sin mitigación frente a TREX y ZNE; ¿cuánto se acerca al valor exacto?       |
| VII   | Puertas fraccionales (RZZ) y modo batch; segunda ejecución real.                      |
| VIII  | Reducir la profundidad con un addon (OBP o AQC-Tensor).                               |
| IX    | Migrar el código a las primitivas del lado del cliente y empaquetarlo.                |
| X     | Informe final reproducible: gráficas, cita de Qiskit y del QPU.                       |

Presupuesto del plan Open: 10 min cada 28 días. Hay 3 ejecuciones reales
planificadas, de unos 1–2 min cada una; antes de cada una se estima el uso con
la fórmula de la lección 7.5.

## 4. Repaso espaciado

La portada propone cada día 3–4 preguntas de lecciones ya completadas (las `ask`
existentes), espaciadas en el tiempo: 1, 3, 7 y 21 días. Las que fallas vuelven
antes.

## 5. Nueva portada (un panel, no un índice)

La estructura de la propuesta C, pero **con identidad propia**: sin el azul ni
la letra de IBM, y sin el estilo crema con serifa. Secciones:

1. **Siguiente acción**: la lección pendiente o la misión del proyecto.
2. **Proyecto Ising**: hitos con su estado.
3. **Repaso de hoy**.
4. **Partes**: tarjetas con anillo de progreso.

Pendiente: elegir nombre y paleta entre 2–3 variantes.

## 6. Orden de trabajo

1. **Piloto**: aplicar el ciclo completo a 2 lecciones (1.4 «Tu primer circuito»
   y 2.1 «Construir circuitos»), con sus 2 cuadernos y el hito I del proyecto.
   Pruebas y das tu opinión.
2. Ajustar según tu opinión. Diseñar la portada (variantes de identidad).
3. Extender a las 63 lecciones, parte por parte, verificando cuadernos y audio.
