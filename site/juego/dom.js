// Ayudas para crear nodos sin innerHTML: el texto de un perfil público lo escribe cualquiera.
const SVG = "http://www.w3.org/2000/svg";

function poner(el, props, hijos) {
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.setAttribute("class", v);
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of hijos.flat()) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : String(c));
  }
  return el;
}

export const h = (tag, props, ...hijos) =>
  poner(document.createElement(tag), props, hijos);

export const s = (tag, props, ...hijos) =>
  poner(document.createElementNS(SVG, tag), props, hijos);

export const fmt = (x, d = 2) =>
  Number(x).toLocaleString("es", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });

export const pct = (x, d = 0) => `${fmt(100 * x, d)} %`;

export const reducido = () =>
  matchMedia("(prefers-reduced-motion: reduce)").matches;

// Copia al portapapeles y confirma en el propio botón.
export async function copiar(texto, boton) {
  const antes = boton.textContent;
  try {
    await navigator.clipboard.writeText(texto);
    boton.textContent = "Copiado ✓";
  } catch {
    boton.textContent = "No se pudo copiar";
  }
  setTimeout(() => {
    boton.textContent = antes;
  }, 1800);
}
