# Diseño: esfera de Bloch de la portada

## Intención

Remodelar la esfera de Bloch de la portada para que tenga más profundidad visual y se sienta más clara, sin perder la estética de QuantumShot.

## Objetivos y límites

- Conservar la precesión del vector del qubit y hacer que la esfera se lea mejor como objeto tridimensional.
- Mantener las paletas, variables de color y tipografías actuales.
- No cambiar el texto, la estructura ni el comportamiento del resto de la portada.
- Respetar `prefers-reduced-motion` y el diseño móvil actual.

## Enfoques considerados

1. **SVG con profundidad y precesión (seleccionado):** sumar señales visuales de volumen —meridianos, líneas con distinta profundidad y un vector más claro— al SVG existente. Preserva la idea y animación, con pocos cambios y sin dependencias.
2. **Ilustración estática:** depurar la esfera y reservar el movimiento para interacciones. Es más sobria, pero pierde la precesión que el usuario quiere conservar.

Se eligió el primer enfoque para mejorar la lectura tridimensional sin cambiar la identidad ni quitar el movimiento.

## Restricciones y decisiones pendientes para implementación

- Trabajar en `site/index.html` y `site/index.css`, reutilizando SVG, JavaScript y variables CSS existentes.
- Mantener la órbita del estado; reforzar profundidad con trazos diferenciados y una iluminación sutil derivada de `--acc`.
- El acabado debe funcionar con las paletas claras y oscuras, sin depender de un color fijo.
- Evitar movimiento añadido; conservar el bucle actual y detenerlo si el sistema pide movimiento reducido.
