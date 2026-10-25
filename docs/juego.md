# Misiones, mapa de habilidades y portafolio

En QuantumShot, `site/juego.html` convierte el curso «Del ML al QML» en una ruta
jugable: tres misiones cortas y un reto de transferencia. Cada reto superado
demuestra una habilidad en el mapa y deja una evidencia reproducible en el
portafolio.

## Correr

```sh
QG_CURSO=qml uv run python tools/serve.py
```

Abre <http://localhost:8810/juego.html>. Los experimentos llaman a `POST /run`,
así que la página necesita `serve.py`. En Windows, `serve.py` ejecuta el modo
`run` sin `qgcheck`, porque `qgcheck` usa `fork`; la corrección de los ejercicios
de las lecciones (`check`) requiere Linux o macOS. GitHub Pages no ejecuta
`POST /run`: allí se puede recorrer el mapa y abrir el perfil de ejemplo, que
muestra resultados precomputados.

## Archivos

| Archivo                    | Contenido                                                                       |
| -------------------------- | ------------------------------------------------------------------------------- |
| `site/juego/datos.js`      | Habilidades (con posición fija), misiones con su diseño, insignias, datos.      |
| `site/juego/estado.js`     | Progreso en `localStorage`, recompensas sin duplicados, estados, enlace.        |
| `site/juego/qiskit.js`     | Llamada a `/run` y el código Qiskit de cada experimento.                        |
| `site/juego/misiones.js`   | El ciclo común de una misión y la lógica de cada una: reglas, pistas, gráficos. |
| `site/juego/mapa.js`       | La constelación (SVG con zoom, arrastre y teclado) y su vista en lista.         |
| `site/juego/evidencias.js` | El texto de una evidencia para quien no conoce el juego.                        |
| `site/juego/portafolio.js` | Portafolio personal, vista pública y opciones de compartir.                     |
| `site/juego/app.js`        | Rutas: `#mapa`, `#mision=`, `#copia=`, `#portafolio`, `#publico=`, `#ejemplo`.  |

## Las misiones

| Misión                    | Puente                       | El jugador decide               | Regla para superarla                                         |
| ------------------------- | ---------------------------- | ------------------------------- | ------------------------------------------------------------ |
| La moneda cuántica        | distribución → regla de Born | θ de `ry` y cuántos `1` predice | `P(1)` de `Statevector` a ±0,02 del objetivo, con predicción |
| Cazar el ruido            | Monte Carlo → shots          | shots por estimación            | `√(p(1−p)/N)` ≤ tolerancia y `N` ≤ presupuesto, tras medir   |
| Detector de parecidos     | kernel RBF → kernel cuántico | escala de los datos y `reps`    | aciertos del kernel cuántico ≥ meta (7 u 8 de 8)             |
| Reto: el kernel con ruido | Monte Carlo + kernel         | shots por estimación (máx. 500) | fiabilidad `Φ(Δ/σ_Δ)` ≥ 95 % con los kernels exactos         |

- Todos los números físicos salen de Qiskit (`StatevectorSampler` y
  `Statevector`). Es un simulador: la página lo dice en cada misión y en cada
  evidencia.
- En «Cazar el ruido» y en el reto, la regla usa la fórmula y Qiskit aporta lo
  observado. Con 30 o 20 repeticiones, la dispersión observada fluctúa demasiado
  para decidir con ella.
- En «Detector de parecidos», con `reps = 2` ninguna escala llega a 7 de 8 en
  estos datos (comprobado con Qiskit). Queda como opción para explorar. El RBF
  clásico acierta 8 de 8 y la misión lo muestra: no se afirma ventaja cuántica.
- No hay motor de IA en el proyecto. Las pistas son reglas fijas: tres niveles
  por misión, que dependen de lo último que se midió.

## Progreso y recompensas

- Se guarda en `localStorage` (`qiskit:juego`) y no sale del navegador. La demo
  actual no configura sincronización de cuentas.
- Cada recompensa tiene una clave única (`m1:superada`, `m2:variante:1`…), así
  que repetir una misión no suma XP otra vez. Fallar no quita nada.
- «Demostrada» solo llega con una evidencia de un reto superado. Una lección
  narrada completada o una misión empezada dejan la habilidad en «practicada» o
  «en exploración». La XP cuenta actividad y la interfaz dice que no mide
  dominio.

## Compartir

El enlace público lleva el perfil y las evidencias marcadas como públicas,
codificados en el fragmento `#publico=`. No hay servidor que los guarde y la
vista valida cada campo, porque cualquiera puede escribir un enlace. En
`localhost` la página avisa de que el enlace solo abre en ese equipo. El texto
para LinkedIn se arma con las evidencias públicas y solo se copia: no se publica
nada. `#ejemplo` muestra un perfil de demostración marcado como tal.

## Prueba con usuarios (15 minutos, 3–5 personas)

Que el recorrido funcione en un navegador no dice si engancha. Para eso:

1. Abre `juego.html` con el progreso vacío (ventana privada). Di solo: «Es un
   juego para aprender. Piensa en voz alta».
2. Observa sin ayudar durante la primera misión y anota:
   - si entiende el objetivo sin abrir «¿Necesitas un repaso rápido?»;
   - cuánto tarda en medir por primera vez y si lee el «Qué significa»;
   - dónde se atasca y si pide pistas;
   - qué dice al ver el cierre de la misión.
3. Al terminar la primera misión, pregunta «¿Quieres seguir?» y no sugieras
   cuál. Anota si elige otra misión por su cuenta y cuál.
4. Tres preguntas al final:
   - «Explícame con tus palabras qué hace el ángulo θ».
   - «¿Qué fue lo más frustrante?».
   - «¿Enseñarías tu portafolio a alguien? ¿A quién?».

Señales: entiende la primera misión sin ayuda, elige otra por iniciativa propia
y explica θ con sus palabras.
