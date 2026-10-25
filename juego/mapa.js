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

const POSICIONES_RED = {
  "c-prob": { x: 130, y: 330 },
  "c-mc": { x: 310, y: 190 },
  "c-rbf": { x: 760, y: 220 },
  "q-born": { x: 520, y: 370 },
  "q-shots": { x: 310, y: 540 },
  "q-kernel": { x: 790, y: 440 },
  "t-kshots": { x: 565, y: 665 },
  "g-grad": { x: 895, y: 600 },
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
function arista(a, b, organica) {
  const baja = b.y > a.y + 40;
  const x1 = a.x;
  const y1 = baja ? a.y + 64 : a.y;
  const dx = b.x - x1;
  const dy = b.y - y1;
  const d = Math.hypot(dx, dy);
  const sx = baja ? x1 : x1 + (dx / d) * (R + 8);
  const sy = baja ? y1 : y1 + (dy / d) * (R + 8);
  const ex = b.x - (dx / d) * (R + 10);
  const ey = b.y - (dy / d) * (R + 10);
  if (!organica)
    return {
      d: `M${sx} ${sy} L${ex} ${ey}`,
      medioX: (sx + ex) / 2,
      medioY: (sy + ey) / 2,
    };
  const vx = ex - sx;
  const vy = ey - sy;
  const longitud = Math.hypot(vx, vy) || 1;
  const nx = -vy / longitud;
  const ny = vx / longitud;
  const clave = `${a.id}:${b.id}`;
  const lado = [...clave].reduce((suma, letra) => suma + letra.charCodeAt(0), 0) % 2 ? 1 : -1;
  const curva = Math.min(52, Math.max(12, longitud * 0.12)) * lado;
  const x1c = sx + vx / 3 + nx * curva;
  const y1c = sy + vy / 3 + ny * curva;
  const x2c = sx + (2 * vx) / 3 + nx * curva;
  const y2c = sy + (2 * vy) / 3 + ny * curva;
  const f = (valor) => valor.toFixed(1);
  return {
    d: `M${f(sx)} ${f(sy)} C${f(x1c)} ${f(y1c)} ${f(x2c)} ${f(y2c)} ${f(ex)} ${f(ey)}`,
    medioX: (sx + ex) / 2 + nx * curva * 0.75,
    medioY: (sy + ey) / 2 + ny * curva * 0.75,
  };
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

function redAmbiente(limites) {
  let semilla = 37;
  const azar = () => ((semilla = (semilla * 48271) % 2147483647) - 1) / 2147483646;
  const gauss = () => {
    const radio = Math.sqrt(-2 * Math.log(Math.max(azar(), 1e-9)));
    return radio * Math.cos(2 * Math.PI * azar());
  };
  const grupos = [
    { x: 0.12, y: 0.36 },
    { x: 0.36, y: 0.28 },
    { x: 0.57, y: 0.48 },
    { x: 0.76, y: 0.36 },
    { x: 0.39, y: 0.78 },
  ];
  const puntos = Array.from({ length: 150 }, (_, i) => {
    const grupo = Math.floor(i / 30);
    const centro = grupos[grupo];
    return {
      grupo,
      x: limites.x + Math.max(0.015, Math.min(0.985, centro.x + gauss() * 0.105)) * limites.w,
      y: limites.y + Math.max(0.035, Math.min(0.965, centro.y + gauss() * 0.13)) * limites.h,
    };
  });
  const enlaces = [];
  const usados = new Set();
  const unir = (i, j) => {
    const llave = `${Math.min(i, j)}:${Math.max(i, j)}`;
    if (usados.has(llave)) return;
    usados.add(llave);
    const a = puntos[i];
    const b = puntos[j];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const largo = Math.hypot(dx, dy) || 1;
    const curva = (azar() < 0.5 ? -1 : 1) * Math.min(34, largo * 0.2);
    const cx = (a.x + b.x) / 2 - (dy / largo) * curva;
    const cy = (a.y + b.y) / 2 + (dx / largo) * curva;
    enlaces.push(s("path", {
      class: "malla-enlace",
      d: `M${a.x.toFixed(1)} ${a.y.toFixed(1)} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`,
    }));
  };
  for (let i = 0; i < puntos.length; i++) {
    const cercanos = puntos
      .map((punto, j) => ({ j, d: Math.hypot(punto.x - puntos[i].x, punto.y - puntos[i].y) }))
      .filter(({ j, d }) => j !== i && puntos[j].grupo === puntos[i].grupo && d < 170)
      .sort((a, b) => a.d - b.d)
      .slice(0, 3);
    for (const { j } of cercanos) unir(i, j);
    if (i % 8 === 0) {
      const puente = puntos
        .map((punto, j) => ({ j, d: Math.hypot(punto.x - puntos[i].x, punto.y - puntos[i].y) }))
        .filter(({ j }) => j !== i && puntos[j].grupo !== puntos[i].grupo)
        .sort((a, b) => a.d - b.d)[0];
      if (puente) unir(i, puente.j);
    }
  }
  return s("g", { class: "red-ambiente", "aria-hidden": "true" }, [
    ...enlaces,
    ...puntos.map((punto, i) => s("circle", {
      class: `malla-nodo ${i % 4 === 0 ? "destacado" : ""}`,
      cx: punto.x,
      cy: punto.y,
      r: i % 4 === 0 ? 2.2 : 1.35,
    })),
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
  let pulsoSeleccion = false;
  const seccion = raiz.closest(".constelacion-sec");
  const organica = Boolean(seccion);
  const miniPortafolio = Boolean(raiz.closest(".mapa-mini"));
  const aspecto = seccion?.clientWidth && seccion?.clientHeight
    ? seccion.clientWidth / seccion.clientHeight
    : 1190 / 980;
  const altoRed = 980;
  const anchoRed = Math.max(980, altoRed * aspecto);
  const escalaX = anchoRed / 1190;
  const centroX = 503;
  // El encuadre sigue la proporción del panel y evita el espacio vacío del SVG apaisado.
  const INICIO = organica
    ? { x: centroX - anchoRed / 2, y: -126, w: anchoRed, h: altoRed }
    : { x: -270, y: -90, w: W + 540, h: H + 150 };
  let vb = { ...INICIO };
  const posiciones = Object.fromEntries(
    HABILIDADES.map((x) => {
      const base = organica ? POSICIONES_RED[x.id] : x;
      return [x.id, { ...base, x: centroX + (base.x - centroX) * (organica ? escalaX : 1), id: x.id }];
    }),
  );
  const fondoSvg = fondo();
  const malla = organica || miniPortafolio ? redAmbiente(INICIO) : null;
  const movil = matchMedia("(max-width: 700px), (max-aspect-ratio: 1 / 1)").matches;
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
      zoomBtn("Centrar", "Volver a encuadrar", () => encuadrar()),
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
  // Los botones deslizan el encuadre (240 ms, ease-in-out); el arrastre, la rueda modificada
  // y el pellizco siguen a la mano y cambian el encuadre directamente.
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
    if (seccion) {
      seccion.dataset.vista = v;
      document.body.dataset.mapaVista = v;
    }
    for (const b of barra.querySelectorAll("[data-vista]"))
      b.setAttribute("aria-pressed", String(b.dataset.vista === v));
  }

  // Arrastrar mueve el mapa; Shift + rueda y el pellizco lo acercan sin secuestrar el scroll normal.
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
      if (!e.shiftKey) return;
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
    const a = posiciones[actual.dataset.id];
    let mejor = null;
    let dmin = Infinity;
    for (const b of HABILIDADES) {
      const posicion = posiciones[b.id];
      const dx = posicion.x - a.x;
      const dy = posicion.y - a.y;
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
    const animarSeleccion = pulsoSeleccion && !quieto.matches;
    pulsoSeleccion = false;
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
    const bandas = organica ? [] : GRUPOS.map((g) => {
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
        const a = posiciones[r];
        const destino = posiciones[b.id];
        const curva = arista(a, destino, organica);
        const puente = b.puente?.[r];
        const enfocada = enfoque && enfoque.has(a.id) && enfoque.has(b.id);
        const clase = [
          "arista",
          puente && "puente",
          b.proximamente && "tenue",
          enfoque && (enfocada ? "resaltada" : "atenuada"),
          animarSeleccion && enfocada && "pulso-seleccion",
        ]
          .filter(Boolean)
          .join(" ");
        aristas.push(
          s("path", {
            class: clase,
            d: curva.d,
            fill: "none",
            "marker-end": "url(#flecha)",
          }),
        );
        if (puente)
          etiquetas.push(
            s("text", {
              class: `etq-puente${enfoque && !(enfoque.has(a.id) && enfoque.has(b.id)) ? " atenuada" : ""}`,
              x: curva.medioX + 10,
              y: curva.medioY + 4,
              text: puente,
            }),
          );
      }
    }

    const nodos = HABILIDADES.map((x) => {
      const e = estados[x.id];
      const posicion = posiciones[x.id];
      const etiquetaAncho = x.corto.length * 10 + 26;
      const clase = [
        "nodo",
        `e-${e}`,
        x.id === sel && "sel",
        animarSeleccion && x.id === sel && "pulso-seleccion",
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
          transform: `translate(${posicion.x} ${posicion.y})`,
          tabindex: "0",
          role: "button",
          "data-id": x.id,
          "aria-pressed": String(x.id === sel),
          "aria-label": `${x.nombre}: ${nombreEstado(e)}${pre.has(x.id) ? ", requisito de la selección" : ""}`,
          onclick: () => seleccionar(x.id, { animar: true }),
          onkeydown: (ev) => {
            if (ev.key === "Enter" || ev.key === " ") {
              ev.preventDefault();
              seleccionar(x.id);
            }
          },
        },
        s("circle", { class: "blanco", r: R + 16 }),
        forma(e),
        organica
          ? [
              s("rect", { class: "etiqueta-nodo", x: R + 12, y: -20, width: etiquetaAncho, height: 40, rx: 10 }),
              s("text", { class: "nombre", x: R + 24, y: 6, "text-anchor": "start", text: x.corto }),
            ]
          : [
              s("text", { class: "nombre", y: R + 22, text: x.corto }),
              s("text", { class: "estado", y: R + 38, text: nombreEstado(e) }),
            ],
      );
    });

    svg.replaceChildren(
      s(
        "defs",
        null,
        s(
          "linearGradient",
          { id: "g-malla", gradientUnits: "userSpaceOnUse", x1: INICIO.x, y1: 0, x2: INICIO.x + INICIO.w, y2: 0 },
          s("stop", { offset: "0%", class: "g-violeta" }),
          s("stop", { offset: "52%", class: "g-cian" }),
          s("stop", { offset: "100%", class: "g-ambar" }),
        ),
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
      fondoSvg,
      ...(malla ? [malla] : []),
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
  function seleccionar(
    id,
    { avisar = true, resaltar: r = true, animar = false } = {},
  ) {
    sel = id;
    resaltar = r;
    pulsoSeleccion = animar;
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
