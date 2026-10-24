// La constelación de habilidades: un SVG con zoom, desplazamiento y selección, y una lista
// equivalente para móvil y lectores de pantalla. Cada estado tiene forma y etiqueta propias,
// no solo color. Las posiciones vienen de datos.js y no cambian con el progreso.
import { ESTADOS, GRUPOS, HABILIDADES } from "./datos.js";
import { h, s } from "./dom.js";

const W = 900;
const H = 680;
const R = 20;
const BANDAS = {
  clasico: [52, 232],
  cuantico: [292, 472],
  puentes: [520, 668],
};

const porId = Object.fromEntries(HABILIDADES.map((x) => [x.id, x]));

function ancestros(id, acc = new Set()) {
  for (const r of porId[id].requiere) {
    if (!acc.has(r)) {
      acc.add(r);
      ancestros(r, acc);
    }
  }
  return acc;
}

// Las aristas salen por debajo de la etiqueta cuando bajan, para no tachar el texto.
function arista(a, b) {
  const baja = b.y > a.y + 40;
  const x1 = a.x;
  const y1 = baja ? a.y + 64 : a.y;
  const dx = b.x - x1;
  const dy = b.y - y1;
  const d = Math.hypot(dx, dy);
  const [sx, sy] = baja
    ? [x1, y1]
    : [x1 + (dx / d) * (R + 8), y1 + (dy / d) * (R + 8)];
  return [sx, sy, b.x - (dx / d) * (R + 10), b.y - (dy / d) * (R + 10)];
}

function estrella(r) {
  const p = [];
  for (let k = 0; k < 10; k++) {
    const a = (Math.PI / 5) * k - Math.PI / 2;
    const rr = k % 2 ? r * 0.45 : r;
    p.push(`${(rr * Math.cos(a)).toFixed(1)},${(rr * Math.sin(a)).toFixed(1)}`);
  }
  return p.join(" ");
}

function forma(estado) {
  switch (estado) {
    case "demostrada":
      return [
        s("circle", { class: "halo", r: R + 12 }),
        s("polygon", { class: "fig", points: estrella(R + 6) }),
      ];
    case "practicada":
      return [s("circle", { class: "fig", r: R })];
    case "explorando":
      return [
        s("circle", { class: "fig aro", r: R }),
        s("path", { class: "fig", d: `M0,${-R} A${R},${R} 0 0 1 0,${R} Z` }),
      ];
    case "disponible":
      return [s("circle", { class: "fig aro", r: R })];
    case "bloqueada":
      return [
        s("circle", { class: "fig aro", r: R - 4 }),
        s("rect", {
          class: "candado",
          x: -5,
          y: -1,
          width: 10,
          height: 8,
          rx: 1.5,
        }),
        s("path", { class: "candado-arco", d: "M-3,-1 v-3 a3,3 0 0 1 6,0 v3" }),
      ];
    default:
      return [s("circle", { class: "fig aro", r: R - 8 })];
  }
}

const nombreEstado = (e) =>
  e === "sinevidencia" ? "Sin evidencia compartida" : ESTADOS[e].nombre;

// Fondo de estrellas fijo (semilla constante): decoración, no información.
function fondo() {
  let x = 7;
  const rnd = () => ((x = (x * 16807) % 2147483647) - 1) / 2147483646;
  const capa = (n, r0, r1, cls) =>
    Array.from({ length: n }, () =>
      s("circle", {
        class: cls,
        cx: -W + rnd() * 3 * W,
        cy: -H + rnd() * 3 * H,
        r: r0 + rnd() * (r1 - r0),
      }),
    );
  return s("g", { class: "cielo", "aria-hidden": "true" }, [
    ...capa(260, 0.4, 0.9, "lejana"),
    ...capa(90, 0.8, 1.5, "media"),
    ...capa(22, 1.4, 2.4, "cercana"),
  ]);
}

const zoomBtn = (t, etiqueta, fn) =>
  h("button", {
    type: "button",
    class: "zbtn",
    "aria-label": etiqueta,
    title: etiqueta,
    text: t,
    onclick: fn,
  });

export function crearMapa(
  raiz,
  { estadoDe, alSeleccionar, titulo = "Mapa de habilidades" },
) {
  let sel = null;
  let destacar = null;
  let resaltar = true;
  // El encuadre deja margen a los lados: ahí flotan la meta y la ficha de la habilidad.
  const INICIO = { x: -270, y: -90, w: W + 540, h: H + 150 };
  let vb = { ...INICIO };
  const movil = matchMedia("(max-width: 700px)").matches;
  let vista = movil ? "lista" : "mapa";

  const botonVista = (v, t) =>
    h("button", {
      type: "button",
      class: "seg",
      "data-vista": v,
      text: t,
      onclick: () => cambiarVista(v),
    });
  const barra = h(
    "div",
    { class: "mapa-barra" },
    h(
      "div",
      { class: "segs", role: "group", "aria-label": "Vista del mapa" },
      botonVista("mapa", "Constelación"),
      botonVista("lista", "Lista"),
    ),
    h(
      "div",
      { class: "zooms" },
      zoomBtn("−", "Alejar", () => zoom(1.25)),
      zoomBtn("+", "Acercar", () => zoom(0.8)),
      zoomBtn("⤢", "Volver a encuadrar", () => encuadrar()),
    ),
  );
  const svg = s("svg", {
    class: "constelacion",
    role: "group",
    "aria-label": `${titulo}. Usa Tab para recorrer las habilidades y Enter para seleccionar.`,
  });
  const lienzo = h("div", { class: "mapa-lienzo" }, svg);
  const lista = h("div", { class: "mapa-lista" });
  const leyenda = h(
    "ul",
    { class: "leyenda", "aria-label": "Leyenda de estados" },
    ["disponible", "explorando", "practicada", "demostrada", "bloqueada"].map(
      (e) =>
        h(
          "li",
          { class: `e-${e}` },
          s(
            "svg",
            { viewBox: "-26 -26 52 52", "aria-hidden": "true" },
            forma(e),
          ),
          ESTADOS[e].nombre,
        ),
    ),
  );
  raiz.replaceChildren(barra, lienzo, lista, leyenda);

  function aplicarVB() {
    svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
  }
  // Los botones deslizan el encuadre (240 ms, ease-in-out) para no perder la orientación; la rueda,
  // el arrastre y el pellizco lo cambian directo, porque siguen a la mano.
  const quieto = matchMedia("(prefers-reduced-motion: reduce)");
  let anim = 0;
  let rumbo = null; // destino de la animación en curso
  function irA(destino, suave) {
    cancelAnimationFrame(anim);
    rumbo = null;
    if (!suave || quieto.matches) {
      vb = destino;
      return aplicarVB();
    }
    const desde = { ...vb };
    rumbo = destino;
    const t0 = performance.now();
    const paso = (t) => {
      const q = Math.min(1, (t - t0) / 240);
      const e = q < 0.5 ? 4 * q * q * q : 1 - (-2 * q + 2) ** 3 / 2;
      for (const k of ["x", "y", "w", "h"])
        vb[k] = desde[k] + (destino[k] - desde[k]) * e;
      aplicarVB();
      if (q < 1) anim = requestAnimationFrame(paso);
      else rumbo = null;
    };
    anim = requestAnimationFrame(paso);
  }
  // Sin centro (botones) el zoom se anima; con centro (rueda) o con suave=false (pellizco) es directo.
  function zoom(f, cx, cy, suave = cx === undefined) {
    const base = suave && rumbo ? rumbo : vb;
    cx ??= base.x + base.w / 2;
    cy ??= base.y + base.h / 2;
    const w = Math.min(Math.max(base.w * f, 320), INICIO.w * 1.4);
    const k = w / base.w;
    irA(
      {
        x: cx - (cx - base.x) * k,
        y: cy - (cy - base.y) * k,
        w,
        h: base.h * k,
      },
      suave,
    );
  }
  function encuadrar() {
    irA({ ...INICIO }, true);
  }
  function cambiarVista(v) {
    vista = v;
    raiz.dataset.vista = v;
    for (const b of barra.querySelectorAll("[data-vista]"))
      b.setAttribute("aria-pressed", String(b.dataset.vista === v));
  }

  // Desplazar arrastrando (ratón o un dedo), zoom con la rueda o pellizcando.
  const punteros = new Map();
  let pellizco = 0;
  const aSvg = (e) => {
    const r = svg.getBoundingClientRect();
    return [
      vb.x + ((e.clientX - r.left) / r.width) * vb.w,
      vb.y + ((e.clientY - r.top) / r.height) * vb.h,
    ];
  };
  svg.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      zoom(e.deltaY > 0 ? 1.12 : 0.89, ...aSvg(e));
    },
    { passive: false },
  );
  svg.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".nodo")) return;
    irA({ ...vb }, false); // agarrar el mapa detiene la animación del encuadre
    svg.setPointerCapture(e.pointerId);
    punteros.set(e.pointerId, [e.clientX, e.clientY]);
  });
  svg.addEventListener("pointermove", (e) => {
    const prev = punteros.get(e.pointerId);
    if (!prev) return;
    const r = svg.getBoundingClientRect();
    if (punteros.size === 2) {
      punteros.set(e.pointerId, [e.clientX, e.clientY]);
      const [a, b] = [...punteros.values()];
      const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (pellizco) zoom(pellizco / d, undefined, undefined, false);
      pellizco = d;
      return;
    }
    vb.x -= ((e.clientX - prev[0]) / r.width) * vb.w;
    vb.y -= ((e.clientY - prev[1]) / r.height) * vb.h;
    punteros.set(e.pointerId, [e.clientX, e.clientY]);
    aplicarVB();
  });
  const soltar = (e) => {
    punteros.delete(e.pointerId);
    pellizco = 0;
  };
  svg.addEventListener("pointerup", soltar);
  svg.addEventListener("pointercancel", soltar);

  // Con las flechas el foco salta al nodo más cercano en esa dirección.
  svg.addEventListener("keydown", (e) => {
    const dir = {
      ArrowRight: [1, 0],
      ArrowLeft: [-1, 0],
      ArrowDown: [0, 1],
      ArrowUp: [0, -1],
    }[e.key];
    const actual = e.target.closest?.(".nodo");
    if (!dir || !actual) return;
    e.preventDefault();
    const a = porId[actual.dataset.id];
    let mejor = null;
    let dmin = Infinity;
    for (const b of HABILIDADES) {
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const avance = dx * dir[0] + dy * dir[1];
      if (avance <= 0) continue;
      const d = avance + 2 * Math.abs(dx * dir[1] - dy * dir[0]);
      if (d < dmin) {
        dmin = d;
        mejor = b;
      }
    }
    if (mejor) svg.querySelector(`.nodo[data-id="${mejor.id}"]`).focus();
  });

  function dibujar() {
    const estados = Object.fromEntries(
      HABILIDADES.map((x) => [x.id, estadoDe(x)]),
    );
    const pre = sel ? ancestros(sel) : new Set();
    const abre = sel
      ? HABILIDADES.filter((b) => b.requiere.includes(sel)).map((b) => b.id)
      : [];
    const enfoque = sel && resaltar ? new Set([sel, ...pre, ...abre]) : null;
    const foco = document.activeElement?.closest?.(".nodo")?.dataset.id;

    // Cada grupo es una nebulosa: una elipse difusa con el nombre de la constelación.
    const bandas = GRUPOS.map((g) => {
      const [y0, y1] = BANDAS[g.id];
      return s(
        "g",
        { class: `banda b-${g.id}` },
        s("ellipse", {
          cx: W / 2,
          cy: (y0 + y1) / 2,
          rx: W / 2 + 20,
          ry: (y1 - y0) / 2 + 26,
          fill: `url(#neb-${g.id})`,
        }),
        s("text", { x: 30, y: y0 + 18, text: g.nombre.toUpperCase() }),
      );
    });

    const aristas = [];
    const etiquetas = [];
    for (const b of HABILIDADES) {
      for (const r of b.requiere) {
        const a = porId[r];
        const [x1, y1, x2, y2] = arista(a, b);
        const puente = b.puente?.[r];
        const clase = [
          "arista",
          puente && "puente",
          b.proximamente && "tenue",
          enfoque &&
            (enfoque.has(a.id) && enfoque.has(b.id) ? "resaltada" : "atenuada"),
        ]
          .filter(Boolean)
          .join(" ");
        aristas.push(
          s("line", {
            class: clase,
            x1,
            y1,
            x2,
            y2,
            "marker-end": "url(#flecha)",
          }),
        );
        if (puente)
          etiquetas.push(
            s("text", {
              class: `etq-puente${enfoque && !(enfoque.has(a.id) && enfoque.has(b.id)) ? " atenuada" : ""}`,
              x: x1 + 10,
              y: (y1 + y2) / 2 + 4,
              text: puente,
            }),
          );
      }
    }

    const nodos = HABILIDADES.map((x) => {
      const e = estados[x.id];
      const clase = [
        "nodo",
        `e-${e}`,
        x.id === sel && "sel",
        pre.has(x.id) && "pre",
        enfoque && !enfoque.has(x.id) && "atenuada",
        x.id === destacar && "recien",
      ]
        .filter(Boolean)
        .join(" ");
      return s(
        "g",
        {
          class: clase,
          transform: `translate(${x.x} ${x.y})`,
          tabindex: "0",
          role: "button",
          "data-id": x.id,
          "aria-pressed": String(x.id === sel),
          "aria-label": `${x.nombre}: ${nombreEstado(e)}${pre.has(x.id) ? ", requisito de la selección" : ""}`,
          onclick: () => seleccionar(x.id),
          onkeydown: (ev) => {
            if (ev.key === "Enter" || ev.key === " ") {
              ev.preventDefault();
              seleccionar(x.id);
            }
          },
        },
        s("circle", { class: "blanco", r: R + 16 }),
        forma(e),
        s("text", { class: "nombre", y: R + 22, text: x.corto }),
        s("text", { class: "estado", y: R + 38, text: nombreEstado(e) }),
      );
    });

    svg.replaceChildren(
      s(
        "defs",
        null,
        s(
          "marker",
          {
            id: "flecha",
            viewBox: "0 0 10 10",
            refX: 8,
            refY: 5,
            markerWidth: 7,
            markerHeight: 7,
            orient: "auto-start-reverse",
          },
          s("path", { class: "punta", d: "M0,0 L10,5 L0,10 z" }),
        ),
        // Las flechas puente bajan de la fila clásica a la cuántica: ámbar arriba, cian abajo.
        s(
          "linearGradient",
          {
            id: "g-puente",
            gradientUnits: "userSpaceOnUse",
            x1: 0,
            y1: 170,
            x2: 0,
            y2: 330,
          },
          s("stop", { offset: "0%", class: "g-clasico" }),
          s("stop", { offset: "100%", class: "g-cuantico" }),
        ),
        ...GRUPOS.map((g) =>
          s(
            "radialGradient",
            { id: `neb-${g.id}` },
            s("stop", { offset: "0%", class: "neb-c" }),
            s("stop", { offset: "100%", class: "neb-b" }),
          ),
        ),
      ),
      fondo(),
      ...bandas,
      ...aristas,
      ...etiquetas,
      ...nodos,
    );
    aplicarVB();
    if (foco) svg.querySelector(`.nodo[data-id="${foco}"]`)?.focus();

    lista.replaceChildren(
      ...GRUPOS.map((g) =>
        h(
          "section",
          null,
          h("h3", { text: g.nombre }),
          h(
            "ul",
            null,
            HABILIDADES.filter((x) => x.grupo === g.id).map((x) => {
              const e = estados[x.id];
              return h(
                "li",
                null,
                h(
                  "button",
                  {
                    type: "button",
                    class: `item e-${e}${x.id === sel ? " sel" : ""}${pre.has(x.id) ? " pre" : ""}`,
                    "aria-pressed": String(x.id === sel),
                    onclick: () => seleccionar(x.id),
                  },
                  s(
                    "svg",
                    { viewBox: "-26 -26 52 52", "aria-hidden": "true" },
                    forma(e),
                  ),
                  h("span", { class: "n", text: x.nombre }),
                  h("span", { class: "est", text: nombreEstado(e) }),
                  pre.has(x.id)
                    ? h("span", { class: "req", text: "requisito" })
                    : null,
                ),
              );
            }),
          ),
        ),
      ),
    );
  }

  // Al abrir el mapa se selecciona la meta sin atenuar el resto; un clic sí enfoca sus requisitos.
  function seleccionar(id, { avisar = true, resaltar: r = true } = {}) {
    sel = id;
    resaltar = r;
    dibujar();
    if (avisar && id) alSeleccionar?.(porId[id]);
  }

  cambiarVista(vista);
  dibujar();
  return {
    seleccionar,
    actualizar(opts = {}) {
      destacar = opts.destacar ?? null;
      dibujar();
    },
    encuadrar,
    get seleccion() {
      return sel;
    },
  };
}
