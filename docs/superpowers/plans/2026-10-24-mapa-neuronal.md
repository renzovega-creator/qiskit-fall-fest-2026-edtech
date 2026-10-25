# Red neuronal de habilidades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

**Goal:** Acercar el mapa a las referencias clara y oscura, mantener el selector
global de tema, animar brevemente las relaciones al seleccionar una habilidad y
mostrar la red ambiental también en «Tu mapa» del portafolio.

**Architecture:** Conservar la topología de habilidades del SVG y sumar una
malla neuronal estática en el mapa a pantalla completa y en el mapa mini del
portafolio; dejar rectas las conexiones y preservar posiciones y estados del
portafolio. La composición sigue la referencia y adopta la variante clara u
oscura del selector global. La selección de puntero marca durante un instante el
nodo y sus conexiones destacadas; el CSS desactiva el movimiento con
`prefers-reduced-motion`.

**Tech Stack:** JavaScript de módulos, SVG y CSS existentes.

**Spec:** `docs/superpowers/specs/2026-10-24-mapa-neuronal-design.md`

## Global Constraints

- Implementar con el SVG, JavaScript y CSS existentes; no agregar dependencias.
- Limitar la composición flotante al mapa a pantalla completa; en el portafolio
  añadir solo la malla ambiental detrás del mapa existente.
- Mantener el contenido textual legible en ambos temas y los estados
  distinguibles además del color.
- La animación será corta, basada en propiedades del SVG que no cambien el
  diseño, y se desactivará con movimiento reducido.
- Conservar controles, lista accesible, diseño móvil, foco de teclado y
  compatibilidad con `prefers-reduced-motion`.
- No agregar ni ejecutar pruebas automatizadas.

## Review Focus

- **Movimiento reducido:** comprobar por inspección que la preferencia del
  sistema apaga pulso, halo y transiciones del panel.
- **Teclado y puntero:** confirmar que Enter/Espacio conserva la selección
  accesible sin activar la animación reservada a clic/tap.
- **Dependencias:** revisar que las conexiones destacadas corresponden al nodo
  seleccionado y que la ficha continúa abriéndose y cerrándose igual.
- **Curvas y etiquetas:** revisar que curvas, puntas y rótulos de puentes no se
  solapen de forma que impida leer el mapa.
- **Alcance visual:** verificar que la pantalla completa sigue el tema global y
  que «Tu mapa» recibe solo la malla de fondo, sin cambiar sus habilidades ni la
  vista móvil de lista.

---

### Task 1: Curvas estables y respuesta de selección en el SVG

**Files:**

- Modify: `site/juego/mapa.js`

**Interfaces:**

- Consumes: `HABILIDADES`, `GRUPOS`, `ESTADOS` y el selector
  `seleccionar(id, opciones)` existentes.
- Produces: elementos SVG `<path class="arista">` con curvas deterministas
  dentro de `.constelacion-sec`, segmentos rectos en mapas del portafolio,
  marcadores y clases de selección; el pulso se añade solo al seleccionar desde
  puntero.

- [x] **Step 1: Convertir la geometría de las aristas** en una ruta SVG curva y
      determinista solo dentro de `.constelacion-sec`; preservar segmentos
      rectos en los mapas del portafolio, la separación respecto a los nombres
      de nodos y el mismo punto medio para las etiquetas de puentes.
- [x] **Step 2: Enlazar la selección a las clases de pulso.** El clic/tap marca
      temporalmente el nodo elegido y las aristas resaltadas; la selección con
      teclado y la selección inicial actualizan los estados sin animar.
- [x] **Step 3: Revisar el cambio** con `git diff --check` e inspeccionar el
      fragmento de JavaScript modificado, incluidos los manejadores de teclado y
      el movimiento reducido.

### Task 2: Composición clara/oscura y movimiento de red

**Files:**

- Modify: `site/juego-mapa.css`

**Interfaces:**

- Consumes: clases `arista`, `resaltada`, `atenuada`, `nodo`, `sel` y
  `pulso-seleccion` emitidas por `mapa.js`.
- Produces: variantes clara y azul noche con acentos cian/violeta, composición
  de referencia, malla ambiental también en `.mapa-mini`, curvas legibles, halo
  de nodo, animación corta de conexiones y ficha de selección.

- [x] **Step 1: Definir el tema y la composición** de `.constelacion-sec` según
      el selector global, con variantes clara y oscura, título, ficha amplia y
      controles horizontales como en las referencias.
- [x] **Step 2: Estilizar aristas y estados** para que conexiones enfocadas
      brillen sobre las atenuadas, conservando la codificación de estado y las
      etiquetas.
- [x] **Step 3: Añadir el pulso** con escala/opacity en el halo del nodo y
      opacity en sus conexiones; dentro de `prefers-reduced-motion: reduce`,
      quitar la animación y transiciones del mapa.
- [x] **Step 4: Revisar el diff** para confirmar el alcance por ruta, los
      controles de 44 px, los estados de foco y la anulación de movimiento
      reducido.

### Task 3: Generar y publicar la versión de Pages

**Files:**

- Deploy: salida de `tools/pages.py` en la rama de publicación `gh-pages`.

**Interfaces:**

- Consumes: cambios revisados en `main` y el flujo de publicación existente.
- Produces: versión desplegada con el mapa actualizado; `main` mantiene el
  código fuente y los documentos de diseño/plan.

- [x] **Step 1: Generar la salida de Pages** usando el script existente a partir
      de `main` y revisar los archivos producidos del mapa.
- [x] **Step 2: Integrar en Git** el diseño, el plan y los cambios de la
      interfaz en `main`; publicar únicamente la salida generada en `gh-pages`.
- [x] **Step 3: Confirmar el resultado** con el estado de ambas ramas, el
      resultado del flujo de publicación y una solicitud HTTP de la página
      actualizada.
