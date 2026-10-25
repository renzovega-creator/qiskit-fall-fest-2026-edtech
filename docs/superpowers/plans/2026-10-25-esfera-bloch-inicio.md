# Esfera de Bloch de la portada: plan de implementación

> **Para agentes de implementación:** trabajar paso a paso sobre este plan y la especificación vinculada.

**Objetivo:** remodelar la esfera de Bloch de la portada para comunicar mejor su profundidad y conservar la precesión del vector.

**Arquitectura:** seguir usando el SVG que genera la portada y las reglas CSS existentes. Añadir trazos de profundidad y una iluminación leve con variables del tema, sin dependencias nuevas ni cambios al resto de la página.

**Tecnologías:** SVG, JavaScript y CSS del sitio.

**Especificación:** `docs/superpowers/specs/2026-10-25-esfera-bloch-inicio-design.md`

## Restricciones globales

- Trabajar en `site/index.html` y `site/index.css`, reutilizando SVG, JavaScript y variables CSS existentes.
- Conservar las paletas y tipografías actuales.
- Mantener la precesión del estado y respetar `prefers-reduced-motion`.
- No cambiar el texto, la estructura ni el comportamiento del resto de la portada.

## Puntos de revisión visual

- La esfera sigue siendo legible con todas las paletas claras y oscuras.
- Los trazos de profundidad no compiten con el vector ni con su órbita animada.
- Las etiquetas de los estados siguen viéndose separadas de la esfera y sus ejes.
- La ilustración conserva su proporción y centrado en el espacio disponible.
- En pantallas móviles permanece oculto el SVG, igual que en el diseño actual.

## Archivos y responsabilidades

- `site/index.html`: construye los elementos SVG y anima el estado que precesa.
- `site/index.css`: controla la escala y los trazos del SVG según las variables visuales existentes.

## Tarea 1: Dar profundidad a la esfera existente

**Archivos:**

- Modificar: `site/index.html`, bloque `esfera de Bloch`.
- Modificar: `site/index.css`, reglas `svg.bloch` y `.bloch`.

**Interfaces:**

- Consume: el SVG `#bloch`, las variables de tema actuales y el bucle de precesión existente.
- Produce: la misma ilustración animada con un volumen más claro, legible en las paletas del sitio.

- [x] Añadir al SVG una capa interior y líneas de referencia curvas que sugieran meridianos y diferencien frente y fondo; usar el radio y la inclinación actuales como base.
- [x] Reforzar la separación entre contorno, referencias, órbita y vector con trazos y opacidades CSS derivados de `--acc`, `--acc2`, `--line` y `--muted`.
- [x] Conservar el movimiento y las condiciones actuales de `prefers-reduced-motion`; no añadir animaciones nuevas.
- [x] Mantener la proporción, centrado, texto accesible oculto y regla móvil existente.

La instrucción del espacio de trabajo excluye agregar o ejecutar pruebas si el usuario no lo pide; el alcance no crea pruebas nuevas.
