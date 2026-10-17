// Se carga en <head> para fijar ambos atributos antes de pintar. Sin modo guardado, sigue la preferencia del sistema.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  const MODE = "qiskit:theme",
    PAL = "qiskit:paleta";
  const PALETAS = {
    fosforo: "Fósforo",
    cobre: "Cobre",
    medianoche: "Medianoche",
  };
  const root = document.documentElement;
  const read = (k) => {
    try {
      return localStorage.getItem(k);
    } catch {
      return null;
    }
  };
  const write = (k, v) => {
    try {
      localStorage.setItem(k, v);
    } catch {}
  };
  const sys = () =>
    matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";

  const savedMode = read(MODE),
    savedPal = read(PAL);
  root.dataset.theme =
    savedMode === "light" || savedMode === "dark" ? savedMode : sys();
  root.dataset.paleta = Object.hasOwn(PALETAS, savedPal) ? savedPal : "fosforo";

  const modeLabel = () => (root.dataset.theme === "light" ? "☾" : "☀");
  const modeTitle = () =>
    "Cambiar a tema " + (root.dataset.theme === "light" ? "oscuro" : "claro");
  const paint = () =>
    document.querySelectorAll("[data-theme-ctl]").forEach((c) => {
      c.querySelector("select").value = root.dataset.paleta;
      const b = c.querySelector("button");
      b.textContent = modeLabel();
      b.title = modeTitle();
    });

  window.toggleTheme = () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    write(MODE, root.dataset.theme);
    paint();
    dispatchEvent(new Event("themechange"));
  };
  const setPaleta = (p) => {
    root.dataset.paleta = p;
    write(PAL, p);
    paint();
    dispatchEvent(new Event("themechange"));
  };

  addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-ctl]").forEach((c) => {
      const sel = document.createElement("select");
      sel.setAttribute("aria-label", "Paleta");
      sel.title = "Paleta de colores";
      for (const k in PALETAS) sel.add(new Option(PALETAS[k], k));
      sel.addEventListener("change", () => setPaleta(sel.value));
      const btn = document.createElement("button");
      btn.setAttribute("aria-label", "Tema claro u oscuro");
      btn.addEventListener("click", window.toggleTheme);
      c.classList.add("theme-ctl");
      c.append(sel, btn);
    });
    paint();
  });
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
    if (read(MODE)) return;
    root.dataset.theme = sys();
    paint();
    dispatchEvent(new Event("themechange"));
  });
})();
