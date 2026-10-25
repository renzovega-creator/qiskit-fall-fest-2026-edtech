// Cuenta opcional para llevar el progreso a otro navegador (docs/runner.md#cuentas).
// Sin cuenta no hace peticiones de cuenta. Con la marca qiskit:cuenta, junta el
// progreso antes de pintar y envía los cambios que admite el Worker.
// Las reflexiones (qiskit:reflect) no salen del navegador.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  "use strict";
  const FLAG = "qiskit:cuenta";
  const RETURN_HASH = "#cuenta";
  const SYNC_TIMEOUT_MS = 4000;
  const PUSH_DELAY_MS = 1500;
  const MAX_CODE_BYTES = 20000;

  const LESSON = /^[a-z0-9][a-z0-9-]{0,59}$/;
  const EXERCISE = /^qiskit:exercise:([a-z0-9-]{1,40}\/[a-z0-9-]{1,40})$/;
  const KV =
    /^qiskit:(?:heard:[a-z0-9-]{1,60}|pos:[a-z0-9-]{1,60}|predict:[a-z0-9-]{1,60}:[A-Za-z0-9_-]{1,60}|hitos|misiones|repaso)$/;

  const read = (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  };
  const write = (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {}
  };
  const parse = (raw) => {
    try {
      return JSON.parse(raw);
    } catch {
      return undefined;
    }
  };
  const count = (n) => (Number.isSafeInteger(n) && n >= 0 ? n : 0);

  const listeners = new Set();
  const state = { signedIn: read(FLAG) !== null, busy: false, message: "" };
  const update = (patch) => {
    Object.assign(state, patch);
    listeners.forEach((f) => f());
  };
  const forget = () => {
    try {
      localStorage.removeItem(FLAG);
    } catch {}
    update({ signedIn: false });
  };

  function exerciseBody(value) {
    if (typeof value !== "object" || value === null || Array.isArray(value))
      return null;
    const out = {
      hints: count(value.hints),
      checks: count(value.checks),
      passed: value.passed === true,
      at: count(value.at),
    };
    if (
      typeof value.code === "string" &&
      new Blob([value.code]).size <= MAX_CODE_BYTES
    )
      out.code = value.code;
    return out;
  }

  // Omite valores que harían fallar todo el cuerpo de POST /api/merge.
  function collect(keys) {
    const body = { done: [], exercises: {}, kv: {} };
    for (const key of keys) {
      const value = parse(read(key));
      if (value === undefined) continue;
      const exercise = EXERCISE.exec(key);
      if (key === "qiskit:done") {
        if (Array.isArray(value))
          body.done = value.filter(
            (id) => typeof id === "string" && LESSON.test(id),
          );
      } else if (exercise) {
        const item = exerciseBody(value);
        if (item) body.exercises[exercise[1]] = item;
      } else if (KV.test(key)) {
        body.kv[key] = value;
      }
    }
    return body;
  }

  const allKeys = () => {
    const keys = [];
    try {
      for (let k = 0; k < localStorage.length; k++)
        keys.push(localStorage.key(k));
    } catch {}
    return keys;
  };

  // La respuesta incluye lo enviado y reemplaza los valores locales.
  function adopt(progress) {
    const done = new Set([
      ...(parse(read("qiskit:done")) || []),
      ...progress.done,
    ]);
    write("qiskit:done", JSON.stringify([...done]));
    for (const [id, item] of Object.entries(progress.exercises)) {
      const key = `qiskit:exercise:${id}`;
      const local = parse(read(key)) || {};
      write(
        key,
        JSON.stringify({ ...local, ...item, code: item.code ?? local.code }),
      );
    }
    for (const [key, value] of Object.entries(progress.kv))
      write(key, JSON.stringify(value));
  }

  const api = (method, path, body, options = {}) =>
    fetch(path, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      ...options,
    });

  // 401: la sesión caducó o se cerró en otro sitio.
  const lapsed = (resp) => {
    if (resp.status !== 401) return false;
    forget();
    return true;
  };

  async function sync() {
    const ctl = new AbortController();
    const cut = setTimeout(() => ctl.abort(), SYNC_TIMEOUT_MS);
    try {
      const resp = await api("POST", "/api/merge", collect(allKeys()), {
        signal: ctl.signal,
      });
      if (lapsed(resp)) return;
      if (!resp.ok) throw new Error(String(resp.status));
      if (read(FLAG) === null) write(FLAG, "1");
      adopt((await resp.json()).progress);
      update({ signedIn: true, message: "" });
    } catch {
      update({
        message: "No se pudo sincronizar. Tu progreso sigue en este navegador.",
      });
    } finally {
      clearTimeout(cut);
    }
  }

  const dirty = new Set();
  let timer = null,
    pushing = Promise.resolve();
  function flush({ unloading = false } = {}) {
    clearTimeout(timer);
    timer = null;
    if (!state.signedIn || !dirty.size) return;
    const body = collect(dirty);
    dirty.clear();
    pushing = pushing.then(async () => {
      try {
        const resp = await api("PUT", "/api/progress", body, {
          keepalive: unloading,
        });
        if (!lapsed(resp) && !resp.ok) throw new Error(String(resp.status));
      } catch {
        update({
          message: "No se pudo guardar en tu cuenta. Se reintentará al volver.",
        });
      }
    });
  }
  function changed(key) {
    if (
      !state.signedIn ||
      !(key === "qiskit:done" || EXERCISE.test(key) || KV.test(key))
    )
      return;
    dirty.add(key);
    clearTimeout(timer);
    timer = setTimeout(flush, PUSH_DELAY_MS);
  }
  addEventListener("pagehide", () => flush({ unloading: true }));
  addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flush({ unloading: true });
  });

  const signIn = (provider) => {
    const back = location.pathname + location.search + RETURN_HASH;
    location.href = `/auth/${provider}?return=${encodeURIComponent(back)}`;
  };
  async function signOut() {
    flush();
    await pushing;
    try {
      const resp = await api("POST", "/auth/logout");
      if (!resp.ok) throw new Error(String(resp.status));
      forget();
    } catch {
      update({ message: "No se pudo cerrar la sesión. Inténtalo de nuevo." });
    }
  }
  // Borra la cuenta y lo que guarda. La copia de este navegador se queda.
  async function deleteAccount() {
    clearTimeout(timer);
    dirty.clear();
    await pushing;
    try {
      const resp = await api("DELETE", "/api/me");
      if (!resp.ok && !lapsed(resp)) throw new Error(String(resp.status));
      forget();
      update({
        message: "Cuenta borrada. Tu progreso sigue en este navegador.",
      });
    } catch {
      update({ message: "No se pudo borrar la cuenta. Inténtalo de nuevo." });
    }
  }

  function mount(host) {
    host.classList.add("acct");
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-haspopup", "true");
    button.setAttribute("aria-expanded", "false");
    const menu = document.createElement("div");
    menu.className = "acct-menu";
    menu.hidden = true;
    host.append(button, menu);
    let confirming = false;

    const providerIcon = (provider) => {
      const ns = "http://www.w3.org/2000/svg";
      const marks = {
        google: [
          [
            "#FFC107",
            "M43.611 20.083H42V20H24v8h11.303C33.654 32.658 29.223 36 24 36c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z",
          ],
          [
            "#FF3D00",
            "M6.306 14.691l6.571 4.819C14.655 16.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4c-7.682 0-14.344 4.326-17.694 10.691z",
          ],
          [
            "#4CAF50",
            "M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.143 35.091 26.715 36 24 36c-5.202 0-9.616-3.317-11.286-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z",
          ],
          [
            "#1976D2",
            "M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.089 5.571l.003-.002 6.19 5.238C36.969 39.038 44 34 44 24c0-1.341-.138-2.65-.389-3.917z",
          ],
        ],
        github: [
          [
            "currentColor",
            "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
          ],
        ],
      }[provider];
      const svg = document.createElementNS(ns, "svg");
      svg.setAttribute(
        "viewBox",
        provider === "google" ? "0 0 48 48" : "0 0 24 24",
      );
      svg.setAttribute("aria-hidden", "true");
      svg.setAttribute("focusable", "false");
      marks.forEach(([fill, d]) => {
        const path = document.createElementNS(ns, "path");
        path.setAttribute("d", d);
        path.setAttribute("fill", fill);
        svg.append(path);
      });
      return svg;
    };
    const item = (label, onclick, cls = "", iconName) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = cls;
      if (iconName)
        b.append(providerIcon(iconName), document.createTextNode(label));
      else b.textContent = label;
      b.addEventListener("click", onclick);
      menu.append(b);
    };
    const para = (text) => {
      const p = document.createElement("p");
      p.textContent = text;
      menu.append(p);
    };
    const privacy = () => {
      const a = document.createElement("a");
      a.href = "privacidad.html";
      a.textContent = "Privacidad";
      menu.append(a);
    };
    const close = () => {
      menu.hidden = true;
      button.setAttribute("aria-expanded", "false");
      confirming = false;
      paint();
    };

    function paint() {
      button.textContent = state.signedIn ? "Cuenta ✓" : "Entrar";
      button.title = state.signedIn
        ? "Tu progreso se guarda en tu cuenta"
        : "Guarda tu progreso y llévalo a otro navegador";
      menu.textContent = "";
      if (state.message) para(state.message);
      if (!state.signedIn) {
        para(
          "Entra para guardar tu progreso en una cuenta y verlo en otro navegador. Es opcional.",
        );
        item("Entrar con Google", () => signIn("google"), "provider", "google");
        item("Entrar con GitHub", () => signIn("github"), "provider", "github");
      } else if (confirming) {
        para(
          "Se borra tu cuenta y todo lo que guarda. Lo que hay en este navegador se queda.",
        );
        item(
          "Sí, borrar",
          async () => {
            confirming = false;
            await deleteAccount();
          },
          "danger",
        );
        item(
          "Cancelar",
          () => {
            confirming = false;
            paint();
          },
          "cancel",
        );
      } else {
        item("Cerrar sesión", signOut);
        item(
          "Borrar mi cuenta",
          () => {
            confirming = true;
            paint();
            menu.querySelector(".cancel").focus();
          },
          "danger",
        );
      }
      privacy();
    }

    button.addEventListener("click", () => {
      menu.hidden = !menu.hidden;
      button.setAttribute("aria-expanded", String(!menu.hidden));
      if (menu.hidden) close();
    });
    // Las teclas del menú no son atajos de la lección.
    host.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !menu.hidden) {
        close();
        button.focus();
      }
      e.stopPropagation();
    });
    // En captura: el clic de un elemento del menú lo repinta, y ya no estaría dentro de `host` al llegar aquí.
    document.addEventListener(
      "click",
      (e) => {
        if (!menu.hidden && !host.contains(e.target)) close();
      },
      true,
    );
    listeners.add(paint);
    paint();
  }
  addEventListener("DOMContentLoaded", () =>
    document.querySelectorAll("[data-account]").forEach(mount),
  );

  // Con la marca, o al volver del proveedor, se junta antes de que la página lea su progreso.
  const returning = location.hash === RETURN_HASH;
  if (returning)
    history.replaceState(null, "", location.pathname + location.search);
  const ready = state.signedIn || returning ? sync() : Promise.resolve();

  window.QGAccount = { ready, changed };
})();
