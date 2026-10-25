// Portafolio: la vista personal (perfil, progreso, evidencias, compartir) y la pública de solo
// lectura, que se reconstruye entera a partir del enlace.
import {
  AVATARES,
  COLORES,
  HABILIDADES,
  INSIGNIAS,
  LECCIONES,
  MISIONES,
} from "./datos.js";
import { copiar, h } from "./dom.js";
import {
  codificar,
  datosPublicos,
  desbloqueada,
  estadoHabilidad,
  estadoPublico,
  leccionesHechas,
  superada,
  xpTotal,
} from "./estado.js";
import { describir } from "./evidencias.js";
import { crearMapa } from "./mapa.js";
import { fichaEvidencia } from "./misiones.js";

const contables = HABILIDADES.filter((x) => !x.proximamente);
const local = () => ["localhost", "127.0.0.1", ""].includes(location.hostname);
const ARCHIVOS_AVATAR = ["psi", "atom", "wave", "theta", "orbit", "star"];
const NOMBRES_AVATAR = ["Psi", "Átomo", "Onda", "Theta", "Órbita", "Estrella"];
const NOMBRES_COLOR = {
  acc: "Cian",
  acc2: "Ámbar",
  acc3: "Lima",
  blue: "Azul",
  violet: "Violeta",
};

const imagenAvatar = (id, diferida = false) => {
  const indice = Math.max(AVATARES.indexOf(id), 0);
  return h("img", {
    class: "avatar-img",
    src: new URL(`./avatares/${ARCHIVOS_AVATAR[indice]}.png`, import.meta.url)
      .href,
    alt: "",
    decoding: "async",
    draggable: "false",
    ...(diferida ? { loading: "lazy" } : {}),
  });
};

export const enlacePublico = (datos) =>
  `${location.origin}${location.pathname}#publico=${codificar(datos)}`;

export function abrirEvidencia(e, opts = {}) {
  const dlg = h(
    "dialog",
    { class: "dlg-evidencia", "aria-label": "Evidencia" },
    h("button", {
      type: "button",
      class: "cerrar",
      "aria-label": "Cerrar",
      text: "✕",
      onclick: () => dlg.close(),
    }),
    fichaEvidencia(e, opts),
  );
  dlg.addEventListener("close", () => dlg.remove());
  dlg.addEventListener("click", (ev) => {
    if (ev.target === dlg) dlg.close();
  });
  document.body.append(dlg);
  dlg.showModal();
}

function avatar(perfil, grande = false) {
  return h(
    "span",
    {
      class: `avatar${grande ? " grande" : ""}`,
      style: `--av: var(--${COLORES.includes(perfil.color) ? perfil.color : "acc"})`,
      "aria-hidden": "true",
    },
    imagenAvatar(perfil.avatar),
  );
}

function insignias(ganadas, { mostrarBloqueadas }) {
  return h(
    "ul",
    { class: "insignias" },
    INSIGNIAS.filter((x) => mostrarBloqueadas || ganadas[x.id]).map((x) =>
      h(
        "li",
        { class: ganadas[x.id] ? "ganada" : "pendiente" },
        h("span", { class: "ico", "aria-hidden": "true", text: x.icono }),
        h("b", { text: x.nombre }),
        h("span", { class: "crit", text: x.criterio }),
        h("span", {
          class: "cuando",
          text: ganadas[x.id]
            ? ganadas[x.id] === true
              ? "Obtenida"
              : `Obtenida el ${ganadas[x.id]}`
            : "Por conseguir",
        }),
      ),
    ),
  );
}

export function textoLinkedIn(st, url) {
  const ev = st.evidencias
    .filter((e) => e.publica)
    .map((e) => `• ${describir(e).titulo}.`);
  return [
    "Estoy aprendiendo a conectar estadística y machine learning con computación cuántica con QuantumShot, una app en español hecha con Qiskit.",
    "",
    ev.length
      ? "Lo que he resuelto en sus retos (simulaciones con Qiskit, no hardware):"
      : "Acabo de empezar la primera misión.",
    ...ev,
    "",
    "Lo que más me sorprendió: [escríbelo con tus palabras]",
    ...(url ? ["", `Mi portafolio con las evidencias: ${url}`] : []),
    "",
    "#Qiskit #ComputaciónCuántica #MachineLearning",
  ].join("\n");
}

const radios = (nombre, valores, actual, etiqueta, pinta, nombreDe = String) =>
  h(
    "fieldset",
    { class: "radios elegir" },
    h("legend", { text: etiqueta }),
    valores.map((v) =>
      h(
        "label",
        null,
        h("input", {
          type: "radio",
          name: nombre,
          value: v,
          checked: v === actual,
          "aria-label": `${etiqueta}: ${nombreDe(v)}`,
        }),
        pinta(v),
      ),
    ),
  );

// ---------- vista personal ----------
export function vistaPortafolio(
  raiz,
  { st, guardarSt, alSeleccionarHabilidad, evidencia },
) {
  const hechas = leccionesHechas();
  const estadoDe = (x) => estadoHabilidad(st, x, hechas);
  const demostradas = contables.filter(
    (x) => estadoDe(x) === "demostrada",
  ).length;
  const lecciones = Object.keys(LECCIONES);
  const compartir = (e, boton) =>
    copiar(
      enlacePublico({
        ...datosPublicos(st),
        evidencias: datosPublicos({
          ...st,
          evidencias: [{ ...e, publica: true }],
        }).evidencias,
      }),
      boton,
    );

  // Perfil y edición
  const perfil = st.perfil;
  const cab = h("div", { class: "perfil-cab" });
  const pintarCab = () =>
    cab.replaceChildren(
      avatar(perfil, true),
      h(
        "div",
        null,
        h("h1", { text: perfil.alias || "Tu portafolio" }),
        h("p", {
          class: "bio",
          text:
            perfil.bio ||
            "Añade una presentación breve: quién eres y qué te interesa.",
        }),
      ),
    );
  pintarCab();
  const form = h(
    "form",
    {
      class: "editar",
      onsubmit: (ev) => {
        ev.preventDefault();
        const f = new FormData(ev.currentTarget);
        Object.assign(perfil, {
          alias: String(f.get("alias")).trim().slice(0, 40),
          bio: String(f.get("bio")).trim().slice(0, 160),
          avatar: String(f.get("avatar")),
          color: String(f.get("color")),
        });
        guardarSt();
        pintarCab();
        ev.currentTarget.closest("details").open = false;
        refrescarCompartir();
      },
    },
    h(
      "label",
      null,
      "Nombre o alias",
      h("input", {
        name: "alias",
        maxlength: 40,
        value: perfil.alias,
        autocomplete: "nickname",
      }),
    ),
    h(
      "label",
      null,
      "Presentación breve (160 caracteres)",
      h("textarea", { name: "bio", maxlength: 160, rows: 2, text: perfil.bio }),
    ),
    radios(
      "avatar",
      AVATARES,
      perfil.avatar,
      "Avatar",
      (v) => h("span", { class: "op-av" }, imagenAvatar(v, true)),
      (v) => NOMBRES_AVATAR[Math.max(AVATARES.indexOf(v), 0)],
    ),
    radios(
      "color",
      COLORES,
      perfil.color,
      "Color",
      (v) =>
        h("span", {
          class: "op-color",
          style: `--av: var(--${v})`,
          "aria-label": v,
        }),
      (v) => NOMBRES_COLOR[v] || v,
    ),
    h("button", { type: "submit", class: "primario" }, "Guardar perfil"),
  );

  // Compartir
  const enlace = h("input", {
    id: "enlace-publico",
    type: "url",
    readonly: true,
    class: "enlace",
  });
  const verPublico = h("a", {
    class: "secundario boton",
    text: "Ver como lo verán otros",
  });
  const linkedin = h("textarea", {
    id: "texto-linkedin",
    rows: 10,
    class: "linkedin",
    spellcheck: true,
  });
  function refrescarCompartir() {
    const url = enlacePublico(datosPublicos(st));
    enlace.value = url;
    verPublico.href = url.slice(url.indexOf("#"));
    linkedin.value = textoLinkedIn(st, local() ? null : url);
  }

  const tarjetas = h("div", { class: "evidencias" });
  const pintarTarjetas = () =>
    tarjetas.replaceChildren(
      ...(st.evidencias.length
        ? st.evidencias.map((e) => {
            const d = describir(e);
            return h(
              "article",
              { class: "tarjeta-ev" },
              h("p", {
                class: "kicker",
                text: `${d.mision.titulo} · ${d.fecha}`,
              }),
              h("h3", { text: d.titulo }),
              h(
                "p",
                { class: "chips" },
                d.conceptos.map((c) => h("span", { class: "chip", text: c })),
              ),
              h(
                "label",
                { class: "publica" },
                h("input", {
                  type: "checkbox",
                  checked: e.publica,
                  onchange: (ev) => {
                    e.publica = ev.target.checked;
                    guardarSt();
                    refrescarCompartir();
                  },
                }),
                " Mostrar en mi perfil público",
              ),
              h(
                "div",
                { class: "tarjeta-acc" },
                h(
                  "button",
                  {
                    type: "button",
                    class: "secundario",
                    onclick: () =>
                      abrirEvidencia(e, { alCompartir: compartir }),
                  },
                  "Abrir",
                ),
                h(
                  "button",
                  {
                    type: "button",
                    class: "secundario",
                    onclick: (ev) => compartir(e, ev.currentTarget),
                  },
                  "Copiar enlace",
                ),
              ),
            );
          })
        : [
            h(
              "div",
              { class: "vacio" },
              h("p", {
                text: "Tu portafolio se llena al superar retos: cada uno deja una evidencia que puedes enseñar y que otros pueden reproducir.",
              }),
              h("a", {
                class: "primario boton",
                href: "#mision=m1",
                text: "Empezar «La moneda cuántica»",
              }),
            ),
          ]),
    );
  pintarTarjetas();

  const proximas = MISIONES.filter(
    (m) => desbloqueada(st, m) && !superada(st, m.id),
  );
  const mapaCaja = h("div", { class: "mapa mapa-mini" });

  raiz.replaceChildren(
    h(
      "div",
      { class: "portafolio" },
      h(
        "section",
        { class: "perfil" },
        cab,
        h(
          "details",
          { class: "editar-caja" },
          h("summary", { text: "Editar perfil" }),
          form,
        ),
      ),
      h(
        "section",
        { class: "cifras", "aria-label": "Resumen" },
        h(
          "div",
          null,
          h("b", { text: `${demostradas}/${contables.length}` }),
          "habilidades demostradas en retos",
        ),
        h(
          "div",
          null,
          h("b", {
            text: `${lecciones.filter((l) => hechas.has(l)).length}/${lecciones.length}`,
          }),
          "lecciones narradas completadas",
        ),
        h(
          "div",
          null,
          h("b", {
            text: `${Object.keys(st.insignias).length}/${INSIGNIAS.length}`,
          }),
          "insignias",
        ),
        h(
          "div",
          {
            title:
              "La XP cuenta actividad: predicciones, experimentos y retos. No mide dominio.",
          },
          h("b", { text: String(xpTotal(st)) }),
          "XP de actividad (no mide dominio)",
        ),
      ),
      proximas.length
        ? h(
            "section",
            { class: "proximas" },
            h("h2", { text: "Próximas misiones" }),
            h(
              "ul",
              null,
              proximas.map((m) =>
                h(
                  "li",
                  null,
                  h("a", { href: `#mision=${m.id}`, text: `${m.titulo} →` }),
                  h("span", { text: ` ${m.puente} · ${m.minutos} min` }),
                ),
              ),
            ),
          )
        : null,
      h(
        "section",
        null,
        h("h2", { text: "Evidencias" }),
        h("p", {
          class: "nota",
          text: "Elige cuáles aparecen en tu perfil público. Cada una explica el problema, lo que hiciste, con qué ayuda y cómo reproducirlo.",
        }),
        tarjetas,
      ),
      h("section", null, h("h2", { text: "Tu mapa" }), mapaCaja),
      h(
        "section",
        null,
        h("h2", { text: "Insignias" }),
        insignias(st.insignias, { mostrarBloqueadas: true }),
      ),
      h(
        "section",
        { class: "compartir" },
        h("h2", { text: "Compartir" }),
        h(
          "div",
          { class: "comp-bloque" },
          h("h3", { text: "Enlace a tu portafolio público" }),
          h("label", {
            for: "enlace-publico",
            class: "campo-label",
            text: "Enlace público",
          }),
          h("p", {
            class: "nota",
            text: "El enlace lleva dentro tu perfil y las evidencias marcadas como públicas. No se sube a ningún servidor.",
          }),
          local()
            ? h("p", {
                class: "aviso",
                text: "Estás en tu propio equipo (localhost): este enlace solo se abre aquí. Para que otras personas lo vean, el sitio tiene que estar publicado (docs/deploy.md).",
              })
            : null,
          h(
            "div",
            { class: "fila-enlace" },
            enlace,
            h(
              "button",
              {
                type: "button",
                class: "primario",
                onclick: (ev) => copiar(enlace.value, ev.currentTarget),
              },
              "Copiar enlace",
            ),
            verPublico,
          ),
        ),
        h(
          "div",
          { class: "comp-bloque" },
          h("h3", { text: "Texto para LinkedIn" }),
          h("label", {
            for: "texto-linkedin",
            class: "campo-label",
            text: "Borrador de publicación",
          }),
          h("p", {
            class: "nota",
            text: "Basado en tus evidencias públicas. Edítalo antes de usarlo: no publicamos nada por ti.",
          }),
          linkedin,
          h(
            "button",
            {
              type: "button",
              class: "secundario",
              onclick: (ev) => copiar(linkedin.value, ev.currentTarget),
            },
            "Copiar texto",
          ),
        ),
      ),
    ),
  );
  refrescarCompartir();
  crearMapa(mapaCaja, {
    estadoDe,
    alSeleccionar: alSeleccionarHabilidad,
    titulo: "Tu mapa de habilidades",
  });
  if (evidencia) {
    const e = st.evidencias.find((x) => x.id === evidencia);
    if (e) abrirEvidencia(e, { alCompartir: compartir });
  }
}

// ---------- vista pública ----------
export function vistaPublica(raiz, datos) {
  const estadoDe = estadoPublico(datos.evidencias);
  const demostradas = contables.filter((x) => estadoDe(x) === "demostrada");
  const ganadas = Object.fromEntries(datos.insignias.map((id) => [id, true]));
  const mapaCaja = h("div", { class: "mapa mapa-mini" });
  raiz.replaceChildren(
    h(
      "div",
      { class: "portafolio publico" },
      datos.demo
        ? h("p", {
            class: "aviso demo",
            text: "Perfil de demostración: resultados precomputados de Qiskit; no son de una persona real ni se ejecutan aquí.",
          })
        : null,
      h("p", {
        class: "aviso",
        text: "Vista pública de solo lectura. Las evidencias son retos superados en QuantumShot con el simulador de Qiskit: muestran problemas concretos resueltos, no una certificación.",
      }),
      h(
        "section",
        { class: "perfil" },
        h(
          "div",
          { class: "perfil-cab" },
          avatar(datos.perfil, true),
          h(
            "div",
            null,
            h("h1", { text: datos.perfil.alias || "Portafolio sin nombre" }),
            datos.perfil.bio
              ? h("p", { class: "bio", text: datos.perfil.bio })
              : null,
          ),
        ),
      ),
      h(
        "section",
        null,
        h("h2", { text: "Habilidades demostradas" }),
        demostradas.length
          ? h(
              "ul",
              { class: "lista-hab" },
              demostradas.map((x) =>
                h(
                  "li",
                  null,
                  h("b", { text: `★ ${x.nombre}` }),
                  h("span", { text: x.desc }),
                ),
              ),
            )
          : h("p", {
              class: "nota",
              text: "Aún no hay evidencias compartidas.",
            }),
        mapaCaja,
      ),
      datos.insignias.length
        ? h(
            "section",
            null,
            h("h2", { text: "Insignias" }),
            insignias(ganadas, { mostrarBloqueadas: false }),
          )
        : null,
      h(
        "section",
        null,
        h("h2", { text: "Evidencias" }),
        h(
          "div",
          { class: "fichas" },
          datos.evidencias.map((e) => fichaEvidencia(e, { publica: true })),
        ),
      ),
      h(
        "p",
        { class: "cta-publico" },
        h("a", {
          class: "primario boton",
          href: "#mapa",
          text: "Empieza tu propio portafolio →",
        }),
      ),
    ),
  );
  crearMapa(mapaCaja, { estadoDe, titulo: "Mapa de habilidades del perfil" });
}
