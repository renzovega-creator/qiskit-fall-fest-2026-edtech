# Diseño: red neuronal de habilidades

## Intención

Dar al mapa de habilidades una apariencia de red neuronal, cercana a la referencia oscura enviada, y hacer que la selección de un nodo se sienta conectada con sus requisitos. El mapa es una experiencia de exploración para quienes quieren entender cómo se relacionan las habilidades.

## Objetivos

- Usar un fondo azul noche y acentos cian y violeta en la vista de mapa a pantalla completa y sus controles flotantes, sin cambiar los temas de otras rutas.
- Mantener las posiciones fijas y la interacción actual del SVG.
- Curvar las conexiones para que la red se sienta más orgánica.
- Al seleccionar una habilidad, dar un pulso breve al nodo y animar sutilmente sus conexiones destacadas; mantener visible su ficha.
- Conservar controles, lista accesible, diseño móvil, foco de teclado y compatibilidad con `prefers-reduced-motion`.

## Fuera de alcance

- No mover los nodos de forma continua ni cambiar sus posiciones según la selección.
- No modificar el contenido, progreso, datos o rutas de las habilidades.
- No cambiar los mapas que aparecen dentro del portafolio.

## Enfoques considerados

1. **Red oscura y estable (seleccionado):** conservar la estructura fija, curvar conexiones y animar brevemente el foco al seleccionar. Mantiene referencias espaciales y limita el movimiento a una acción del usuario.
2. **Red con nodos móviles:** simular fuerzas y reorganizar el mapa continuamente. Se acerca a una red viva, pero dificulta encontrar habilidades y añade movimiento constante.
3. **Solo cambio de color:** aplicar el fondo y los colores de la referencia sin cambiar las líneas ni añadir respuesta al clic. Es simple, aunque no comunica la relación entre nodos.

Se eligió el primer enfoque porque la referencia combina una red visualmente rica con nodos legibles y porque el mapa actual ya organiza las dependencias.

## Restricciones y decisiones

- Implementar con el SVG, JavaScript y CSS existentes; no agregar dependencias.
- Limitar la nueva paleta y el tratamiento visual al mapa a pantalla completa; los mapas del portafolio conservan su geometría y estilo.
- Mantener el contenido textual legible sobre el fondo oscuro y los estados distinguibles además del color.
- La animación será corta, basada en propiedades del SVG que no cambien el diseño, y se desactivará con movimiento reducido.

## Trabajo pendiente

Actualizar las aristas SVG para que tengan curvas deterministas, pulir fondo y conexiones, enlazar el pulso a la selección y ajustar la ficha para coincidir con la referencia. Luego revisar el diff y generar la versión de despliegue, respetando la rama `main` y el flujo de GitHub Pages del proyecto.
