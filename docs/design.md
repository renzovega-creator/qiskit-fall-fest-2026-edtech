# Diseño

La portada (`site/index.html`), el reproductor (`site/lesson.html`) y el juego
(`site/juego.html`) comparten un solo tema: la marca «QuantumShot» (eslogan: «Tu
dosis diaria de cuántica»), tres fuentes y una identidad de color en modo claro
y oscuro. Este documento dice qué tokens existen y cómo se usan.

## Archivos

| Archivo               | Contenido                                                               |
| --------------------- | ----------------------------------------------------------------------- |
| `site/theme.css`      | Los tokens de color y de fuente, la marca y el control de tema.         |
| `site/theme.js`       | Fija paleta y modo antes de pintar y construye el control de tema.      |
| `site/index.css`      | Estilos de la portada.                                                  |
| `site/app.css`        | Estilos del reproductor.                                                |
| `site/universo.css`   | La identidad común: colores del par, cabecera con la ruta, superficies. |
| `tests/theme_test.py` | Prueba de navegador: contraste, páginas, paleta guardada.               |

Las páginas cargan `theme.css` antes de su propia hoja, `universo.css` después
de ella y `theme.js` en `<head>`.

## Identidad: el par clásico ↔ cuántico

`universo.css` fija los colores de todo el sitio con el selector
`html[data-paleta][data-theme]`, que gana a las paletas de `theme.css`; las
variables derivadas de `:root` (`--fg`, `--panel`, `--line-strong`…) se
recalculan solas. El color tiene significado: **ámbar** (`--clasico`) para lo
clásico y **cian** (`--cuantico`) para lo cuántico y para las acciones. Los
neutros son casi grises, con un tinte frío. El modo oscuro invierte la
luminosidad con los mismos tonos. Del control de tema solo se muestra el botón
claro/oscuro; el selector de paleta queda oculto.

## Paleta y modo

El lector elige dos cosas y las dos se guardan una vez en `localStorage`:

| Clave           | Valores                                        | Sin guardar  |
| --------------- | ---------------------------------------------- | ------------ |
| `qiskit:paleta` | `catppuccin`, `fosforo`, `cobre`, `medianoche` | `catppuccin` |
| `qiskit:theme`  | `light`, `dark`                                | `light`      |

`theme.js` copia los valores a `data-paleta` y `data-theme` de `<html>` antes de
que el navegador pinte. `theme.css` define los tokens en ocho bloques,
`[data-paleta="…"][data-theme="…"]`. Un valor guardado que no existe se ignora.
La selección anterior se conserva; Catppuccin solo es el valor inicial.

Todo elemento `[data-theme-ctl]` recibe un selector de paleta y el botón de
modo, uno junto al otro. Las dos páginas lo tienen en su barra superior. En
pantallas de 600 px o menos el selector muestra solo el color de acento de la
paleta. Al cambiar paleta o modo, `theme.js` lanza el evento `themechange` en
`window`; `engine.js` lo usa para volver a dibujar los lienzos.

Cada paleta cambia el fondo, la tinta y los acentos. Catppuccin usa Mocha en
modo oscuro y Latte en modo claro; los acentos de Latte se oscurecen para
conservar contraste WCAG AA.

| Paleta       | Acento `acc` | Segundo acento `acc2` |
| ------------ | ------------ | --------------------- |
| `catppuccin` | malva        | teal                  |
| `fosforo`    | verde lima   | turquesa              |
| `cobre`      | naranja      | violeta               |
| `medianoche` | turquesa     | rosa                  |

## Tokens

Los valores de cada paleta están en `site/theme.css`. Los tokens son los mismos
en las ocho combinaciones.

| Token                                     | Uso                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `--bg`                                    | Fondo de la página.                                                                                              |
| `--bg2`                                   | Fondo de código en línea, botones y casillas.                                                                    |
| `--card`                                  | Tarjetas y paneles. Los alias `--panel`, `--fig-bg`, `--code-bg` y `--node` valen lo mismo.                      |
| `--stage`                                 | Escenario del reproductor. También es el color del texto sobre un color con nombre, como la letra de una puerta. |
| `--line`                                  | Bordes y separadores.                                                                                            |
| `--ink`                                   | Texto principal. `--fg` vale lo mismo.                                                                           |
| `--muted`                                 | Texto secundario.                                                                                                |
| `--acc`, `--acc-ink`                      | Acento de la paleta y el texto que se pone encima.                                                               |
| `--acc2`, `--acc3`                        | Segundo y tercer acento. `--acc3` es el dorado.                                                                  |
| `--bad`                                   | Error. `--red` vale lo mismo.                                                                                    |
| `--blue`, `--teal`, `--violet`, `--green` | Colores con nombre del reproductor.                                                                              |
| `--glow`                                  | Resplandor de la tarjeta destacada.                                                                              |
| `--display`, `--sans`, `--mono`           | Fuentes de títulos, de texto y de código.                                                                        |

### Colores con nombre

El reproductor llama a los colores de las lecciones por su nombre: `fg`,
`muted`, `blue`, `gold`, `teal`, `red`, `violet`, `green`, `grid` y `axis`.
`engine.js` los convierte en `var(--nombre)` y en las macros de KaTeX `\fg{…}`,
`\blue{…}` y las demás, que aplican la clase `c-<nombre>` de `app.css`. Cada
nombre es un token y sale de la paleta activa:

| Nombre                            | Token de origen                   |
| --------------------------------- | --------------------------------- |
| `fg`                              | `--ink`                           |
| `muted`                           | `--muted`                         |
| `gold`                            | `--acc3`                          |
| `red`                             | `--bad`                           |
| `blue`, `teal`, `violet`, `green` | Valor propio de cada paleta.      |
| `grid`                            | `--blue` mezclado con `--stage`.  |
| `axis`                            | `--muted` mezclado con `--stage`. |

Otros tokens, como `--fg-soft`, `--line-strong`, `--wire`, `--emph-bg`,
`--box-bg` y `--seg`, se derivan de los anteriores con `color-mix()` en
`theme.css`. `--card-text` usa ese mismo valor que `--fg-soft` en Catppuccin
Latte para mantener el contraste AA.

## Reglas de uso

- Un color de una hoja o de un script es un token: `var(--acc)`, nunca un valor
  hexadecimal. Un fondo translúcido se escribe con `color-mix()` sobre
  `transparent`.
- Un color nuevo se añade a `theme.css` en las ocho combinaciones y pasa
  `tests/theme_test.py` antes de usarse.
- En atributos SVG de presentación `var(--x)` no vale: `engine.js` lo pone como
  estilo. Un lienzo lee el color con `cssv('nombre')` cada vez que se dibuja.
- El texto va sobre `--bg`, `--bg2`, `--card` o `--stage` y alcanza 4,5:1 en las
  cuatro. Los colores de acento que se usan como texto también.
- Las líneas de ejes y de cables llevan significado y alcanzan 3:1 sobre
  `--stage` y `--card`. Las rejillas y los bordes son decoración y no se miden.
- La marca es `<a class="brand"><span class="dot"></span>QuantumShot</a>`, con
  el estilo de `theme.css`, en las dos páginas. En el reproductor, en pantallas
  de 600 px o menos, el punto se oculta para dejar sitio al título.
- Los títulos usan `--display` (Bricolage Grotesque), el texto `--sans` (Inter)
  y el código `--mono` (JetBrains Mono). Las tres páginas las cargan de
  `site/vendor/fonts.css`, en variable y solo con los rangos `latin` y
  `latin-ext`. Las fórmulas usan las fuentes de KaTeX.

## Contraste

Criterio: WCAG 2.x AA. El texto necesita 4,5:1; los ejes y los cables, 3:1.
`tests/theme_test.py` lee cada token en el navegador, en las ocho combinaciones,
y falla si alguno queda por debajo. Cada celda es la peor razón entre las cuatro
superficies (`--bg`, `--bg2`, `--card`, `--stage`); `axis` y `wire` se miden
sobre `--stage` y `--card`, y `acc-ink/acc` es el texto del botón sobre su
fondo.

| token         | fosforo dark | fosforo light | cobre dark | cobre light | medianoche dark | medianoche light | catppuccin dark | catppuccin light |
| ------------- | -----------: | ------------: | ---------: | ----------: | --------------: | ---------------: | --------------: | ---------------: |
| `ink`         |        15.08 |         14.33 |      14.69 |       14.63 |           14.56 |            14.88 |            8.69 |             6.57 |
| `fg-soft`     |        11.69 |         10.12 |      11.44 |       10.34 |           11.31 |            10.60 |            6.95 |             4.88 |
| `card-text`   |         9.73 |          7.75 |       9.54 |        7.88 |            9.43 |             8.08 |            5.92 |             4.88 |
| `muted`       |         5.94 |          4.80 |       5.93 |        5.03 |            5.77 |             4.87 |            5.65 |             5.14 |
| `acc`         |        13.27 |          4.63 |       7.35 |        4.62 |           11.55 |             4.61 |            6.19 |             4.71 |
| `acc2`        |         9.55 |          4.63 |       7.51 |        5.21 |            6.45 |             5.19 |            8.44 |             4.84 |
| `gold`        |        10.40 |          4.67 |      12.05 |        4.66 |           10.24 |             4.69 |            9.89 |             5.03 |
| `red`         |         6.96 |          4.63 |       7.00 |        5.36 |            6.35 |             5.40 |            5.43 |             4.63 |
| `blue`        |         7.99 |          4.92 |       7.85 |        4.90 |            7.82 |             4.93 |            5.97 |             5.29 |
| `teal`        |         9.55 |          4.63 |       9.20 |        4.68 |           11.55 |             4.61 |            8.44 |             4.82 |
| `violet`      |         7.64 |          5.23 |       7.51 |        5.21 |            7.48 |             5.25 |            6.19 |             5.10 |
| `green`       |        10.03 |          4.69 |       9.86 |        4.67 |            9.82 |             4.70 |            8.46 |             4.66 |
| `acc-ink/acc` |        12.89 |          5.41 |       7.57 |        5.41 |           11.34 |             5.36 |            8.07 |             5.73 |
| `axis`        |         3.86 |          3.24 |       3.86 |        3.34 |            3.76 |             3.28 |            3.57 |             3.29 |
| `wire`        |         3.86 |          3.24 |       3.86 |        3.34 |            3.76 |             3.28 |            3.57 |             3.29 |

Para repetir la medición:

```sh
mise run install
uv run python tests/theme_test.py --table
```

La misma prueba carga la portada y tres lecciones, cada una en su primer y
último paso, en las ocho combinaciones y a 1366x768 y 390x844. Exige que la
consola no registre errores y que ningún `#scene > .blk` quede fuera de
`#stage`. `--shots CARPETA` guarda una captura de cada carga.
