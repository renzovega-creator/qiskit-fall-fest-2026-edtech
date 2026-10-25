// Enrutador de juego.html. Rutas en el fragmento de la URL:
//   #mapa · #mision=<id> · #copia=<json> · #portafolio · #publico=<datos> · #ejemplo
import { DEMO, ESTADOS, LECCIONES, MISIONES } from "./datos.js";
import { h } from "./dom.js";
import {
  cargar,
  decodificar,
  desbloqueada,
  estadoHabilidad,
  guardar,
  habilidad,
  leccionesHechas,
  mision,
  proximaMeta,
  superada,
  validarPublico,
  xpTotal,
} from "./estado.js";
import { describir } from "./evidencias.js";
import { crearMapa } from "./mapa.js";
import { abrirMision } from "./misiones.js";
import { abrirEvidencia, vistaPortafolio, vistaPublica } from "./portafolio.js";

const st = cargar();
const guardarSt = () => guardar(st);
const vista = document.querySelector("#vista");
const xpPill = document.querySelector("#xp");
let pendiente = {};

function pintarXp() {
  xpPill.textContent = `${xpTotal(st)} XP`;
}

function irA(hash, opts = {}) {
  pendiente = opts;
  if (location.hash === hash) router();
  else location.hash = hash;
}

// ---------- panel de una habilidad ----------
function panelHabilidad(caja, x) {
  const hechas = leccionesHechas();
  const e = estadoHabilidad(st, x, hechas);
  const misiones = MISIONES.filter((m) => m.demuestra.includes(x.id));
  const evidencias = st.evidencias.filter((ev) =>
    mision(ev.m).demuestra.includes(x.id),
  );
  const disponible = misiones.find(
    (m) => desbloqueada(st, m) && !superada(st, m.id),
  );
  const bloqueada = misiones.find((m) => !desbloqueada(st, m));
  const siguiente = x.proximamente
    ? "Esta habilidad llegará con el nivel 3 del curso."
    : disponible
      ? null
      : bloqueada
        ? `Supera ${bloqueada.requiere
            .filter((r) => !superada(st, r))
            .map((r) => `«${mision(r).titulo}»`)
            .join(" y ")} para desbloquearla.`
        : "Ya la demostraste. Puedes repetir la misión con otra configuración.";
  // replaceChildren no ignora null como h(): el panel se arma dentro de un div.
  caja.replaceChildren(
    h(
      "div",
      null,
      h("p", {
        class: `insignia-estado e-${e}`,
        text: `${ESTADOS[e].marca} ${ESTADOS[e].nombre}`,
      }),
      h("h2", { text: x.nombre }),
      h("p", { text: x.desc }),
      x.requiere.length
        ? h(
            "div",
            null,
            h("h3", { text: "Requisitos" }),
            h(
              "ul",
              { class: "reqs" },
              x.requiere.map((r) => {
                const rh = habilidad(r);
                const re = estadoHabilidad(st, rh, hechas);
                return h(
                  "li",
                  { class: `e-${re}` },
                  `${ESTADOS[re].marca} ${rh.nombre}`,
                  h("span", { text: ` · ${ESTADOS[re].nombre.toLowerCase()}` }),
                );
              }),
            ),
          )
        : null,
      misiones.length
        ? h(
            "div",
            null,
            h("h3", { text: "Misiones" }),
            h(
              "ul",
              { class: "mis-lista" },
              misiones.map((m) =>
                h(
                  "li",
                  null,
                  desbloqueada(st, m)
                    ? h("a", { href: `#mision=${m.id}`, text: m.titulo })
                    : h("span", { text: `🔒 ${m.titulo}` }),
                  superada(st, m.id)
                    ? h("span", { class: "ok", text: " ✓ superada" })
                    : null,
                ),
              ),
            ),
          )
        : null,
      x.leccion
        ? h(
            "p",
            { class: "leccion" },
            "Lección narrada: ",
            h("a", {
              href: `lesson.html?l=${x.leccion}`,
              text: LECCIONES[x.leccion],
            }),
            hechas.has(x.leccion) ? " ✓" : "",
          )
        : null,
      h(
        "div",
        null,
        h("h3", { text: "Evidencias" }),
        evidencias.length
          ? h(
              "ul",
              { class: "ev-lista" },
              evidencias.map((ev) =>
                h(
                  "li",
                  null,
                  h(
                    "button",
                    {
                      type: "button",
                      class: "enlace-btn",
                      onclick: () => abrirEvidencia(ev),
                    },
                    describir(ev).titulo,
                  ),
                ),
              ),
            )
          : h("p", {
              class: "nota",
              text: "Todavía ninguna: una evidencia aparece al superar el reto de una misión.",
            }),
      ),
      disponible
        ? h("a", {
            class: "primario boton",
            href: `#mision=${disponible.id}`,
            text: `Siguiente acción: ${disponible.titulo} →`,
          })
        : h("p", { class: "siguiente", text: siguiente }),
    ),
  );
}

// ---------- página del mapa ----------
function tarjetaMision(m) {
  const ok = superada(st, m.id);
  const abierta = desbloqueada(st, m);
  const pasadas = m.variantes.filter((_, i) =>
    st.evidencias.some((e) => e.id === `${m.id}:${i}`),
  ).length;
  return h(
    "article",
    {
      class: `tarjeta-mis${ok ? " superada" : abierta ? " abierta" : " cerrada"}${m.reto ? " es-reto" : ""}`,
    },
    h("p", {
      class: "kicker",
      text: `${m.reto ? "Reto de transferencia" : "Misión"} · ${m.minutos} min`,
    }),
    h("h3", { text: m.titulo }),
    h("p", { class: "puente-t", text: m.puente }),
    h("p", { class: "d", text: m.diseno.objetivo }),
    abierta
      ? h(
          "a",
          {
            class: ok ? "secundario boton" : "primario boton",
            href: `#mision=${m.id}`,
          },
          ok
            ? pasadas < m.variantes.length
              ? `Repetir con otra configuración (${pasadas}/${m.variantes.length})`
              : "Volver a jugar"
            : "Jugar",
        )
      : h("p", {
          class: "candado-t",
          text: `🔒 Requiere ${m.requiere.map((r) => `«${mision(r).titulo}»`).join(" y ")}`,
        }),
  );
}

function vistaMapa(raiz, { destacar } = {}) {
  const hechas = leccionesHechas();
  const meta = proximaMeta(st);
  const detalle = h("aside", { class: "detalle", "aria-live": "polite" });
  const caja = h("div", { class: "mapa" });
  const abiertasSinHacer = MISIONES.filter(
    (m) => desbloqueada(st, m) && !superada(st, m.id),
  );

  raiz.replaceChildren(
    h(
      "section",
      { class: "meta" },
      meta
        ? [
            h("p", {
              class: "kicker",
              text: st.evidencias.length ? "Tu próxima meta" : "Empieza aquí",
            }),
            h("h1", { text: meta.mision.titulo }),
            h("p", { class: "lead", text: meta.mision.diseno.objetivo }),
            h(
              "p",
              { class: "abre" },
              h("b", { text: "Te permitirá: " }),
              meta.abre.length
                ? `desbloquear ${meta.abre.map((x) => `«${x.titulo}»`).join(" y ")}.`
                : meta.mision.diseno.desbloquea,
            ),
            h("a", {
              class: "primario boton grande",
              href: `#mision=${meta.mision.id}`,
              text: `${st.misiones[meta.mision.id]?.inicio ? "Continuar" : "Empezar"} · ${meta.mision.minutos} min →`,
            }),
            abiertasSinHacer.length > 1
              ? h("p", {
                  class: "nota",
                  text: `Tienes ${abiertasSinHacer.length} misiones abiertas: elige la que más te llame.`,
                })
              : null,
          ]
        : [
            h("p", { class: "kicker", text: "Ruta completada" }),
            h("h1", { text: "Superaste la ruta Del ML al QML" }),
            h("p", {
              class: "lead",
              text: "Puedes repetir las misiones con otras configuraciones, compartir tu portafolio o esperar al nivel 3 (gradientes ↔ parameter-shift).",
            }),
            h("a", {
              class: "primario boton grande",
              href: "#portafolio",
              text: "Ver mi portafolio →",
            }),
          ],
    ),
    h(
      "section",
      { class: "constelacion-sec" },
      h(
        "div",
        { class: "sh" },
        h("h2", { text: "Tu constelación" }),
        h("p", {
          class: "nota",
          text: "Cada estrella es una habilidad. Las flechas marcan requisitos; las de trazo largo, puentes entre una idea clásica y su par cuántico.",
        }),
      ),
      h("div", { class: "mapa-y-detalle" }, caja, detalle),
    ),
    h(
      "section",
      { class: "misiones-sec" },
      h(
        "div",
        { class: "sh" },
        h("h2", { text: "Misiones" }),
        h("p", {
          class: "nota",
          text: "Elige entre las abiertas. Cada misión superada deja una evidencia en tu portafolio.",
        }),
      ),
      h("div", { class: "tarjetas" }, MISIONES.map(tarjetaMision)),
    ),
  );

  // El panel de la habilidad flota sobre el mapa: se abre al elegir un nodo y se cierra con ×.
  const cerrar = h("button", {
    type: "button",
    class: "cerrar-detalle",
    "aria-label": "Cerrar",
    text: "×",
    onclick: () => detalle.classList.remove("abierto"),
  });
  const mapa = crearMapa(caja, {
    estadoDe: (x) => estadoHabilidad(st, x, hechas),
    alSeleccionar: (x) => {
      panelHabilidad(detalle, x);
      detalle.prepend(cerrar);
      detalle.classList.add("abierto");
    },
  });
  const inicial = destacar ?? meta?.mision.demuestra[0] ?? "t-kshots";
  mapa.actualizar({ destacar });
  mapa.seleccionar(inicial, { resaltar: false });
  detalle.classList.remove("abierto");
}

// ---------- rutas ----------
function router() {
  let hash;
  try {
    hash = decodeURIComponent(location.hash.slice(1));
  } catch {
    hash = "";
  }
  const [ruta, valor] = hash.includes("=")
    ? [hash.slice(0, hash.indexOf("=")), hash.slice(hash.indexOf("=") + 1)]
    : [hash || "mapa", ""];
  const opts = pendiente;
  pendiente = {};
  for (const a of document.querySelectorAll(".nav a"))
    a.toggleAttribute("aria-current", a.getAttribute("href") === `#${ruta}`);
  document.body.dataset.ruta = ruta;
  pintarXp();
  window.scrollTo(0, 0);

  if (ruta === "mision" || ruta === "copia") {
    let copia = null;
    let m;
    if (ruta === "copia") {
      try {
        copia = JSON.parse(valor);
        m = mision(copia?.m);
        if (
          !m ||
          !Number.isInteger(copia.v) ||
          !m.variantes[copia.v] ||
          typeof copia.p !== "object"
        )
          m = null;
      } catch {
        m = null;
      }
    } else m = mision(valor);
    if (!m) return vistaError("Esa misión no existe.");
    if (!copia && !desbloqueada(st, m))
      return vistaError(
        `«${m.titulo}» está bloqueada: supera antes ${m.requiere
          .filter((r) => !superada(st, r))
          .map((r) => `«${mision(r).titulo}»`)
          .join(" y ")}.`,
      );
    document.title = "QuantumShot";
    return abrirMision(vista, m, {
      st,
      guardarSt,
      copia,
      irA,
      alCambiarProgreso: pintarXp,
    });
  }
  if (ruta === "portafolio") {
    document.title = "QuantumShot";
    return vistaPortafolio(vista, {
      st,
      guardarSt,
      evidencia: opts.evidencia,
      alSeleccionarHabilidad: (x) => irA("#mapa", { destacar: x.id }),
    });
  }
  if (ruta === "publico" || ruta === "ejemplo") {
    let datos;
    try {
      datos = validarPublico(ruta === "ejemplo" ? DEMO : decodificar(valor));
    } catch {
      return vistaError("Este enlace de portafolio está incompleto o dañado.");
    }
    document.title = "QuantumShot";
    return vistaPublica(vista, datos);
  }
  document.title = "QuantumShot";
  vistaMapa(vista, { destacar: opts.destacar });
}

function vistaError(texto) {
  vista.replaceChildren(
    h(
      "section",
      { class: "meta" },
      h("h1", { text: "No se puede abrir" }),
      h("p", { class: "lead", text: texto }),
      h("a", {
        class: "primario boton",
        href: "#mapa",
        text: "Volver al mapa",
      }),
    ),
  );
}

addEventListener("hashchange", router);
router();
