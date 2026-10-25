# Diseño: red neuronal de habilidades

## Intención

Dar al mapa de habilidades una apariencia de red neuronal, cercana a las
referencias clara y oscura enviadas, y hacer que la selección de un nodo se
sienta conectada con sus requisitos. El mapa es una experiencia de exploración
para quienes quieren entender cómo se relacionan las habilidades.

## Objetivos

- Enmarcar la vista de mapa como en la referencia, con título arriba a la
  izquierda, ficha abajo a la derecha y controles horizontales en la parte
  inferior.
- Seguir el selector global de tema: azul noche cuando está oscuro y superficies
  claras cuando está claro; mantener intactos los temas de las demás rutas.
- Dibujar una malla neuronal estática detrás de las habilidades reales, con
  posiciones estables y conexiones curvas.
- Reutilizar la malla como fondo sutil de la sección «Tu mapa» en el portafolio.
- Curvar las conexiones para que la red se sienta más orgánica.
- Al seleccionar una habilidad, dar un pulso breve al nodo y animar sutilmente
  sus conexiones destacadas; mantener visible su ficha.
- Conservar controles, lista accesible, diseño móvil, foco de teclado y
  compatibilidad con `prefers-reduced-motion`.

## Fuera de alcance

- No mover los nodos de forma continua ni cambiar sus posiciones según la
  selección.
- No modificar el contenido, progreso, datos o rutas de las habilidades.
- No cambiar la topología, posiciones, datos o controles de los mapas del
  portafolio; la malla se añade detrás como decoración.

## Enfoques considerados

1. **Red oscura y estable (seleccionado):** conservar la estructura fija, curvar
   conexiones y animar brevemente el foco al seleccionar. Mantiene referencias
   espaciales y limita el movimiento a una acción del usuario.
2. **Red con nodos móviles:** simular fuerzas y reorganizar el mapa
   continuamente. Se acerca a una red viva, pero dificulta encontrar habilidades
   y añade movimiento constante.
3. **Solo cambio de color:** aplicar el fondo y los colores de la referencia sin
   cambiar las líneas ni añadir respuesta al clic. Es simple, aunque no comunica
   la relación entre nodos.

Se eligió el primer enfoque porque la referencia combina una red visualmente
rica con nodos legibles y porque el mapa actual ya organiza las dependencias.

## Restricciones y decisiones

- Implementar con el SVG, JavaScript y CSS existentes; no agregar dependencias.
- Limitar la composición del mapa a pantalla completa; el selector global
  conserva el control claro/oscuro y la malla de «Tu mapa» conserva las
  variables de tema existentes.
- Mantener el contenido textual legible sobre el fondo oscuro y los estados
  distinguibles además del color.
- La animación será corta, basada en propiedades del SVG que no cambien el
  diseño, y se desactivará con movimiento reducido.

## Implementación

Las aristas SVG tienen curvas deterministas, la malla neuronal decora el mapa de
práctica y «Tu mapa», el pulso responde a la selección y la ficha sigue la
referencia. Revisar el diff y generar la versión de despliegue respetando la
rama `main` y el flujo de GitHub Pages del proyecto.
