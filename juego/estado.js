// Progreso del juego en localStorage (qiskit:juego). No sale del navegador: account.js solo
// sincroniza sus claves conocidas.
//
// Cada recompensa tiene una clave única en `premios`, así que repetir una misión no suma dos
// veces. Una habilidad solo pasa a «demostrada» con una evidencia, que crea un reto superado
// según reglas comprobables (misiones.js), nunca la experiencia acumulada.
import { HABILIDADES, MISIONES, XP } from "./datos.js";

const KEY = "qiskit:juego";
const VACIO = () => ({
  v: 1,
  premios: {},
  insignias: {},
  evidencias: [],
  misiones: {},
  perfil: { alias: "", avatar: "ψ", color: "acc", bio: "" },
});

export function cargar() {
  try {
    const st = JSON.parse(localStorage.getItem(KEY));
    if (st && st.v === 1) return { ...VACIO(), ...st };
  } catch {
    // Un valor ilegible se trata como progreso vacío.
  }
  return VACIO();
}

export function guardar(st) {
  try {
    localStorage.setItem(KEY, JSON.stringify(st));
  } catch {
    // Sin almacenamiento (modo privado estricto) el juego sigue, pero no recuerda nada.
  }
}

export const hoy = () => new Date().toLocaleDateString("en-CA");

export const leccionesHechas = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem("qiskit:done")) || []);
  } catch {
    return new Set();
  }
};

export const mision = (id) => MISIONES.find((m) => m.id === id);
export const habilidad = (id) => HABILIDADES.find((h) => h.id === id);
export const datosMision = (st, id) => (st.misiones[id] ??= {});

// Devuelve true si la recompensa es nueva.
export function premiar(st, clave, xp) {
  if (clave in st.premios) return false;
  st.premios[clave] = xp;
  return true;
}

export function darInsignia(st, id) {
  if (st.insignias[id]) return false;
  st.insignias[id] = hoy();
  return true;
}

export const xpTotal = (st) =>
  Object.values(st.premios).reduce((a, b) => a + b, 0);

export const superada = (st, id) => st.evidencias.some((e) => e.m === id);

export const desbloqueada = (st, m) => m.requiere.every((r) => superada(st, r));

// Añade la evidencia de un reto superado. Una variante ya superada no crea otra ni da XP.
export function registrarExito(st, ev) {
  const id = `${ev.m}:${ev.v}`;
  if (st.evidencias.some((e) => e.id === id)) return { nueva: false, xp: 0 };
  const primera = !superada(st, ev.m);
  st.evidencias.push({ ...ev, id, at: hoy(), publica: true });
  const clave = primera ? `${ev.m}:superada` : `${ev.m}:variante:${ev.v}`;
  const xp = primera ? XP.superada : XP.variante;
  premiar(st, clave, xp);
  return { nueva: true, xp, primera };
}

// Estado de una habilidad para el mapa propio.
export function estadoHabilidad(st, h, hechas = leccionesHechas()) {
  if (h.proximamente) return "proximamente";
  const misiones = MISIONES.filter((m) => m.demuestra.includes(h.id));
  if (misiones.some((m) => superada(st, m.id))) return "demostrada";
  if (!misiones.some((m) => desbloqueada(st, m))) return "bloqueada";
  if (
    (h.leccion && hechas.has(h.leccion)) ||
    misiones.some((m) => st.misiones[m.id]?.corrio)
  )
    return "practicada";
  if (misiones.some((m) => st.misiones[m.id]?.inicio)) return "explorando";
  return "disponible";
}

// Estado en una vista pública: solo se sabe lo que demuestran las evidencias compartidas.
export function estadoPublico(evidencias) {
  const demostradas = new Set(
    evidencias.flatMap((e) => mision(e.m)?.demuestra ?? []),
  );
  return (h) =>
    h.proximamente
      ? "proximamente"
      : demostradas.has(h.id)
        ? "demostrada"
        : "sinevidencia";
}

// La próxima meta: la primera misión desbloqueada sin superar, y qué abre al superarla.
export function proximaMeta(st) {
  const m = MISIONES.find((x) => desbloqueada(st, x) && !superada(st, x.id));
  if (!m) return null;
  const abre = MISIONES.filter(
    (x) =>
      x.requiere.includes(m.id) &&
      x.requiere.every((r) => r === m.id || superada(st, r)),
  );
  return { mision: m, abre };
}

// El enlace público lleva el perfil y las evidencias elegidas en el fragmento de la URL: no hay
// servidor que lo guarde.
export function codificar(datos) {
  const bytes = new TextEncoder().encode(JSON.stringify(datos));
  let bin = "";
  for (const b of bytes) bin += String.fromCodePoint(b);
  return btoa(bin).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

export function decodificar(texto) {
  const bin = atob(texto.replaceAll("-", "+").replaceAll("_", "/"));
  const bytes = Uint8Array.from(bin, (c) => c.codePointAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

export function datosPublicos(st) {
  return {
    perfil: st.perfil,
    insignias: Object.keys(st.insignias),
    evidencias: st.evidencias
      .filter((e) => e.publica)
      .map(({ m, v, at, h, pred, p, r }) => ({ m, v, at, h, pred, p, r })),
  };
}

const str = (s, n) => (typeof s === "string" ? s.slice(0, n) : "");
const num = (o) =>
  Object.fromEntries(
    Object.entries(o && typeof o === "object" ? o : {})
      .filter(([, v]) => typeof v === "number" && Number.isFinite(v))
      .slice(0, 12),
  );

// Un enlace público lo puede escribir cualquiera: se aceptan solo campos y tipos conocidos.
export function validarPublico(d) {
  return {
    demo: d?.demo === true,
    perfil: {
      alias: str(d?.perfil?.alias, 40),
      avatar: str(d?.perfil?.avatar, 2),
      color: str(d?.perfil?.color, 8),
      bio: str(d?.perfil?.bio, 200),
    },
    insignias: (Array.isArray(d?.insignias) ? d.insignias : [])
      .filter((s) => typeof s === "string")
      .slice(0, 20),
    evidencias: (Array.isArray(d?.evidencias) ? d.evidencias : [])
      .filter((e) => mision(e?.m) && Number.isInteger(e.v))
      .slice(0, 20)
      .map((e) => ({
        m: e.m,
        v: e.v,
        at: str(e.at, 10),
        h: Number.isInteger(e.h) ? e.h : 0,
        pred: typeof e.pred === "number" ? e.pred : null,
        p: num(e.p),
        r: num(e.r),
      })),
  };
}
