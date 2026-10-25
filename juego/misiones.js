// Las misiones: un ciclo común (predecir → experimentar con Qiskit → observar → pistas →
// demostrar → desbloquear) y la definición de cada una.
//
// Los resultados salen de Qiskit: ejecución local o datos precomputados en Pages. Superar un reto depende de una
// regla escrita aquí sobre esos resultados; las pistas son reglas fijas según lo que el jugador
// acaba de medir.
import { INSIGNIAS, LUNAS, MISIONES, XP } from "./datos.js";
import { DEMO_MODE, parametrosDemo } from "../demo.js";
import { copiar, fmt, h, pct, reducido, s } from "./dom.js";
import {
  darInsignia,
  datosMision,
  desbloqueada,
  habilidad,
  premiar,
  registrarExito,
} from "./estado.js";
import { describir } from "./evidencias.js";
import { codigo, medirMision, phi } from "./qiskit.js";

const P25 = 0.25; // P(1) de la moneda de «Cazar el ruido»: sin²(π/6)
const media = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
function textoConMath(texto) {
  const fragmento = document.createDocumentFragment();
  const patron = /\$([^$]+)\$/g;
  let desde = 0;
  for (const m of texto.matchAll(patron)) {
    fragmento.append(document.createTextNode(texto.slice(desde, m.index)));
    const formula = document.createElement("span");
    formula.innerHTML = window.katex.renderToString(m[1], {
      throwOnError: false,
    });
    fragmento.append(formula);
    desde = m.index + m[0].length;
  }
  fragmento.append(document.createTextNode(texto.slice(desde)));
  return fragmento;
}
const desv = (xs) => {
  const m = media(xs);
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1));
};

// ---------- utilidades de dibujo ----------
function deslizador({
  etiqueta,
  min,
  max,
  paso,
  valor,
  mostrar,
  alCambiar,
  id,
}) {
  const salida = h("output", { for: id, text: mostrar(valor) });
  const input = h("input", {
    type: "range",
    id,
    min,
    max,
    step: paso,
    value: valor,
    oninput: (e) => {
      const v = Number(e.target.value);
      salida.textContent = mostrar(v);
      alCambiar(v);
    },
  });
  return h(
    "div",
    { class: "ctl" },
    h("label", { for: id }, etiqueta, " ", salida),
    input,
  );
}

function ejeX(svg, x0, x1, y, ticks, escala, formato) {
  svg.append(s("line", { class: "eje", x1: x0, x2: x1, y1: y, y2: y }));
  for (const t of ticks) {
    const x = escala(t);
    svg.append(
      s("line", { class: "eje", x1: x, x2: x, y1: y, y2: y + 5 }),
      s("text", { class: "tick", x, y: y + 18, text: formato(t) }),
    );
  }
}

// ---------- 1 · La moneda cuántica ----------
const m1 = {
  ayuda: [
    "Un porcentaje es una probabilidad por 100: 25 % es 0,25, una de cada cuatro veces.",
    "Al medir un qubit sale 0 o 1. La rotación R_Y(θ) lo inclina desde |0⟩ (arriba) hacia |1⟩ (abajo): con 0° siempre sale 0 y con 180° siempre sale 1.",
    "Un shot es una medición. Con 200 shots cuentas cuántas veces salió 1.",
  ],
  inicial: (copia) => copia?.p ?? { theta: 90, shots: 200, seed: 1 },
  objetivo: (v) =>
    `Consigue que el qubit dé 1 con probabilidad ${pct(v.objetivo)} (margen ± 2 puntos).`,
  prediccion: {
    etiqueta: "¿Cuántos 1 saldrán en 200 shots?",
    min: 0,
    max: 200,
  },
  controles(ctx) {
    return deslizador({
      id: "theta",
      etiqueta: "Ángulo θ de la rotación R_Y:",
      min: 0,
      max: 180,
      paso: 1,
      valor: ctx.params.theta,
      mostrar: (v) => `${v}°`,
      alCambiar: (v) => ctx.cambiar({ theta: v }),
    });
  },
  codigo: (p) => codigo.m1(p),
  procesar: (out) => ({
    p1: out.p1,
    shots: out.shots,
    unos: [...out.shots].filter((c) => c === "1").length,
  }),
  dibujar(vis, ctx) {
    const { theta } = ctx.params;
    const a = (theta * Math.PI) / 180;
    const R = 78;
    const dial = s(
      "svg",
      {
        viewBox: "-140 -110 280 220",
        class: "dial",
        role: "img",
        "aria-label": `Qubit inclinado ${theta}° desde |0⟩`,
      },
      s("circle", { class: "esfera", r: R }),
      s("line", { class: "eje", x1: 0, y1: -R - 10, x2: 0, y2: R + 10 }),
      s("text", { class: "ket", x: 0, y: -R - 16, text: "|0⟩" }),
      s("text", { class: "ket", x: 0, y: R + 28, text: "|1⟩" }),
      s("path", {
        class: "arco",
        d: `M0,${-34} A34,34 0 ${a > Math.PI ? 1 : 0} 1 ${(34 * Math.sin(a)).toFixed(1)},${(-34 * Math.cos(a)).toFixed(1)}`,
      }),
      s("line", {
        class: "proy",
        x1: R * Math.sin(a),
        y1: -R * Math.cos(a),
        x2: 0,
        y2: -R * Math.cos(a),
      }),
      s("line", {
        class: "vec",
        x1: 0,
        y1: 0,
        x2: R * Math.sin(a),
        y2: -R * Math.cos(a),
      }),
      s("circle", {
        class: "punta-vec",
        cx: R * Math.sin(a),
        cy: -R * Math.cos(a),
        r: 6,
      }),
      s("text", { class: "theta", x: -136, y: -88, text: `θ = ${theta}°` }),
    );

    const v = ctx.v;
    const res = ctx.res;
    const lluvia = s("svg", {
      viewBox: "0 0 260 250",
      class: "lluvia",
      role: "img",
      "aria-label": res
        ? `${res.unos} unos y ${200 - res.unos} ceros`
        : "Aún no has medido",
    });
    lluvia.append(...columna(10, "0"), ...columna(140, "1"));
    const cuenta0 = s("text", {
      class: "cuenta",
      x: 65,
      y: 22,
      text: res ? "" : "—",
    });
    const cuenta1 = s("text", {
      class: "cuenta",
      x: 195,
      y: 22,
      text: res ? "" : "—",
    });
    lluvia.append(cuenta0, cuenta1);

    const barras = h("div", { class: "barras" });
    const fila = (nombre, valor, clase) =>
      h(
        "div",
        { class: `barra ${clase}` },
        h("span", { class: "bn", text: nombre }),
        h(
          "span",
          { class: "pista-barra" },
          h("span", {
            class: "zona",
            style: `left:${100 * (v.objetivo - 0.02)}%;width:4%`,
          }),
          valor == null
            ? null
            : h("span", {
                class: "relleno",
                style: `transform:scaleX(${Math.max(0, Math.min(1, valor))})`,
              }),
        ),
        h("span", { class: "bv", text: valor == null ? "—" : pct(valor, 1) }),
      );
    barras.append(
      fila("Objetivo", v.objetivo, "obj"),
      fila("P(1) teórica (Statevector)", res?.p1, "teo"),
      fila(
        "Frecuencia observada (200 shots)",
        res ? res.unos / 200 : null,
        "obs",
      ),
    );
    vis.replaceChildren(h("div", { class: "vis-fila" }, dial, lluvia), barras);

    if (!res || ctx.animado) {
      if (res) {
        cuenta0.textContent = String(200 - res.unos);
        cuenta1.textContent = String(res.unos);
        for (const [i, b] of [...res.shots].entries())
          lluvia.append(gota(b, i, res.shots));
      }
      return;
    }
    // Los shots caen en el orden en que Qiskit los midió.
    ctx.animado = true;
    const n = [0, 0];
    const lote = reducido() ? 200 : 4;
    let i = 0;
    const paso = () => {
      for (let k = 0; k < lote && i < 200; k++, i++) {
        const b = res.shots[i];
        n[b]++;
        lluvia.append(gota(b, i, res.shots));
      }
      cuenta0.textContent = String(n[0]);
      cuenta1.textContent = String(n[1]);
      if (i < 200) requestAnimationFrame(paso);
    };
    paso();
  },
  feedback(ctx) {
    const { res, v, pred } = ctx;
    const sig = Math.sqrt(200 * res.p1 * (1 - res.p1));
    const esperado = 200 * res.p1;
    const dentro = Math.abs(res.p1 - v.objetivo) <= 0.02;
    return [
      pred == null
        ? null
        : `Predijiste ${pred} ${pred === 1 ? "uno" : "unos"}; salieron ${res.unos}.`,
      `La regla de Born da $P(1)=\\sin^2(\\theta/2)=${fmt(res.p1, 3)}$: se esperaban $${fmt(esperado, 0)}\\pm${fmt(sig, 0)}$ unos (un error típico, $\\sqrt{N\\,p(1-p)}$).`,
      `La frecuencia observada, $\\hat p=${fmt(res.unos / 200, 3)}$, no es la probabilidad: con otra semilla saldría otro número cerca de ${fmt(esperado, 0)}.`,
      dentro
        ? `Tu moneda da ${pct(res.p1, 1)} y el objetivo es ${pct(v.objetivo)}: está dentro del margen. Pulsa «Comprobar el reto».`
        : `Tu moneda da ${pct(res.p1, 1)} y el objetivo es ${pct(v.objetivo)}: todavía fuera del margen de ± 2 puntos.`,
    ];
  },
  evaluar({ res, v, pred }) {
    if (pred == null)
      return { ok: false, texto: "Anota una predicción antes de medir." };
    const ok = Math.abs(res.p1 - v.objetivo) <= 0.02;
    return ok
      ? {
          ok,
          texto: `P(1) = ${fmt(res.p1, 3)}, a menos de 0,02 del objetivo ${fmt(v.objetivo, 2)}.`,
        }
      : {
          ok,
          texto: `P(1) = ${fmt(res.p1, 3)} y el objetivo es ${fmt(v.objetivo, 2)} ± 0,02. Ajusta θ y vuelve a medir.`,
        };
  },
  pista({ res, v, params }, nivel) {
    const t = v.objetivo;
    if (nivel === 1)
      return res
        ? `Con θ = ${params.theta}°, P(1) = ${fmt(res.p1, 3)}. Necesitas ${fmt(t, 2)}: ${res.p1 > t ? "disminuye" : "aumenta"} θ. Más ángulo inclina el qubit hacia |1⟩.`
        : "Elige cualquier ángulo y mide: el resultado te dirá si te pasaste o te quedaste corto.";
    if (nivel === 2)
      return `P(1) = sin²(θ/2). Para P(1) = ${fmt(t, 2)} necesitas sin(θ/2) = √${fmt(t, 2)} ≈ ${fmt(Math.sqrt(t), 3)}.`;
    return `θ = 2·arcsin(√${fmt(t, 2)}) ≈ ${fmt((2 * Math.asin(Math.sqrt(t)) * 180) / Math.PI, 0)}°. Ponlo y mide.`;
  },
  evidencia: ({ res }) => ({
    p1: Math.round(res.p1 * 1e4) / 1e4,
    unos: res.unos,
  }),
  insignias({ res, pred }) {
    const sig = Math.sqrt(200 * res.p1 * (1 - res.p1));
    return pred != null && Math.abs(pred - res.unos) <= Math.max(sig, 1)
      ? ["prediccion-certera"]
      : [];
  },
  // Cada medida usa la semilla siguiente; la evidencia guarda la que se usó.
  trasMedir(ctx) {
    if (!DEMO_MODE) ctx.params.seed = ctx.resParams.seed + 1;
  },
};

const columna = (x, t) => [
  s("rect", { class: "columna", x, y: 30, width: 110, height: 190, rx: 10 }),
  s("text", { class: "ket", x: x + 55, y: 242, text: t }),
];

// La gota i ocupa el siguiente hueco libre de su columna.
function gota(b, i, todos) {
  let k = 0;
  for (let j = 0; j < i; j++) if (todos[j] === b) k++;
  const x = (b === "1" ? 140 : 10) + 10 + (k % 10) * 9.5;
  const y = 212 - Math.floor(k / 10) * 9;
  return s("circle", { class: `gota g${b}`, cx: x + 4, cy: y, r: 3.6 });
}

// ---------- 2 · Cazar el ruido ----------
const LY = (e) => 180 - (Math.min(e, 0.15) / 0.15) * 160;
const m2 = {
  ayuda: [
    "El error típico dice cuánto se aleja, en promedio, una estimación del valor real.",
    "La raíz cuadrada deshace el cuadrado: √4 = 2 y √100 = 10.",
    "Aquí la moneda es la de 25 % de la misión anterior: P(1) = 0,25 exactamente.",
  ],
  inicial: (copia) => copia?.p ?? { shots: 100, reps: 30, seed: 100 },
  objetivo: (v) =>
    `Estima P(1) = 0,25 con un error típico ≤ ${fmt(v.tol, 3)} sin pasar de ${v.presupuesto} shots por estimación.`,
  prediccion: {
    etiqueta: "¿Cuántos shots crees que necesitas?",
    min: 1,
    max: 5000,
  },
  controles(ctx) {
    const pres = h("div", { class: "presupuesto" });
    const pintar = () => {
      const n = ctx.params.shots;
      const pasa = n > ctx.v.presupuesto;
      pres.replaceChildren(
        h(
          "span",
          { class: `pres-barra${pasa ? " exceso" : ""}` },
          h("span", {
            style: `width:${Math.min(100, (100 * n) / ctx.v.presupuesto)}%`,
          }),
        ),
        h("span", {
          text: `${n} de ${ctx.v.presupuesto} shots de presupuesto${pasa ? " · te pasas" : ""}`,
        }),
      );
    };
    pintar();
    return h(
      "div",
      null,
      deslizador({
        id: "shots",
        etiqueta: "Shots por estimación N:",
        min: 10,
        max: 2000,
        paso: 10,
        valor: ctx.params.shots,
        mostrar: (v) => String(v),
        alCambiar: (v) => {
          ctx.cambiar({ shots: v });
          pintar();
        },
      }),
      pres,
    );
  },
  codigo: (p) => codigo.m2(p),
  procesar: (out) => ({
    est: out.estimaciones,
    sigmaObs: desv(out.estimaciones),
    media: media(out.estimaciones),
  }),
  dibujar(vis, ctx) {
    const { res, v } = ctx;
    const W = 520;
    const X = (p) => 30 + ((p - 0.1) / 0.3) * (W - 60);
    const tira = s("svg", {
      viewBox: `0 0 ${W} 130`,
      class: "grafico",
      role: "img",
      "aria-label": res
        ? `30 estimaciones con dispersión ${fmt(res.sigmaObs, 3)}`
        : "Aún no has medido",
    });
    tira.append(
      s("rect", {
        class: "zona-obj",
        x: X(P25 - v.tol),
        y: 18,
        width: X(P25 + v.tol) - X(P25 - v.tol),
        height: 76,
      }),
      s("line", { class: "real", x1: X(P25), x2: X(P25), y1: 16, y2: 96 }),
      s("text", {
        class: "nota",
        x: X(P25) + 6,
        y: 11,
        text: "P(1) = 0,25 (teórico)",
      }),
    );
    ejeX(
      tira,
      30,
      W - 30,
      100,
      [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
      X,
      (t) => fmt(t, 2),
    );
    if (res)
      res.est.forEach((p, i) =>
        tira.append(
          s("circle", {
            class: "punto",
            cx: X(Math.min(0.4, Math.max(0.1, p))),
            cy: 30 + (i % 6) * 11,
            r: 5,
          }),
        ),
      );

    const curva = s("svg", {
      viewBox: `0 0 ${W} 232`,
      class: "grafico",
      role: "img",
      "aria-label": "Error típico frente a número de shots",
    });
    const LX = (n) =>
      46 + ((Math.log10(n) - 1) / (Math.log10(2000) - 1)) * (W - 70);
    let d = "";
    for (let n = 10; n <= 2000; n *= 1.08)
      d += `${d ? "L" : "M"}${LX(n).toFixed(1)},${LY(Math.sqrt((P25 * (1 - P25)) / n)).toFixed(1)}`;
    curva.append(
      s("line", { class: "eje", x1: 46, x2: 46, y1: 20, y2: 180 }),
      s("line", {
        class: "meta",
        x1: 46,
        x2: W - 24,
        y1: LY(v.tol),
        y2: LY(v.tol),
      }),
      s("text", {
        class: "nota",
        x: 52,
        y: LY(v.tol) - 6,
        text: `objetivo ≤ ${fmt(v.tol, 3)}`,
      }),
      s("line", {
        class: "pres",
        x1: LX(v.presupuesto),
        x2: LX(v.presupuesto),
        y1: 20,
        y2: 180,
      }),
      s("text", {
        class: "nota",
        x: LX(v.presupuesto) + 4,
        y: 30,
        text: "presupuesto",
      }),
      s("path", { class: "teo", d }),
      s("text", {
        class: "nota teo-t",
        x: LX(14),
        y: LY(0.13),
        text: "√(p(1−p)/N), teórico",
      }),
      s("text", {
        class: "tick y",
        x: 40,
        y: LY(0.15) + 4,
        text: "0,15",
      }),
      s("text", {
        class: "tick y",
        x: 40,
        y: LY(0) + 4,
        text: "0",
      }),
    );
    ejeX(curva, 46, W - 24, 180, [10, 30, 100, 300, 1000, 2000], LX, String);
    for (const [n, e] of ctx.datos.puntos ?? [])
      curva.append(
        s(
          "circle",
          { class: "punto", cx: LX(n), cy: LY(e), r: 5 },
          s("title", { text: `N = ${n}: σ observada ${fmt(e, 4)}` }),
        ),
      );
    curva.append(
      s("text", {
        class: "nota",
        x: 52,
        y: 226,
        text: "● dispersión observada en tus ejecuciones · eje N logarítmico",
      }),
    );
    vis.replaceChildren(
      h("p", {
        class: "vis-t",
        text: "30 estimaciones de P(1), cada una con N shots",
      }),
      tira,
      h("p", { class: "vis-t", text: "Error típico frente a N" }),
      curva,
    );
  },
  feedback({ res, params, v, pred }) {
    const st = Math.sqrt((P25 * (1 - P25)) / params.shots);
    return [
      pred == null ? null : `Tu predicción: ${pred} shots.`,
      `Con N = ${params.shots}, las 30 estimaciones se dispersan σ = ${fmt(res.sigmaObs, 4)} (observado en Qiskit). La fórmula de Monte Carlo da √(0,25·0,75/${params.shots}) = ${fmt(st, 4)}.`,
      `Ninguna estimación es «la» probabilidad: su media (${fmt(res.media, 3)}) se acerca a 0,25 y cada una se desvía por el ruido de disparo.`,
      st <= v.tol
        ? params.shots <= v.presupuesto
          ? "Precisión suficiente y dentro del presupuesto. Pulsa «Comprobar el reto»."
          : "Precisión suficiente, pero te pasas del presupuesto: ¿cuántos shots puedes ahorrar?"
        : `Todavía no llegas a σ ≤ ${fmt(v.tol, 3)}.`,
    ];
  },
  evaluar({ params, v }) {
    const st = Math.sqrt((P25 * (1 - P25)) / params.shots);
    if (st > v.tol)
      return {
        ok: false,
        texto: `Con N = ${params.shots} el error típico es ${fmt(st, 4)}, mayor que ${fmt(v.tol, 3)}.`,
      };
    if (params.shots > v.presupuesto)
      return {
        ok: false,
        texto: `N = ${params.shots} pasa del presupuesto de ${v.presupuesto} shots.`,
      };
    return {
      ok: true,
      texto: `σ = ${fmt(st, 4)} ≤ ${fmt(v.tol, 3)} con ${params.shots} shots, dentro del presupuesto. (Se evalúa con la fórmula: la σ observada con 30 repeticiones fluctúa alrededor de un 13 %.)`,
    };
  },
  pista({ res, params, v }, nivel) {
    if (nivel === 1)
      return res
        ? `Con N = ${params.shots} tus estimaciones se dispersan σ ≈ ${fmt(res.sigmaObs, 3)}; necesitas ≤ ${fmt(v.tol, 3)}. ${res.sigmaObs > v.tol ? "Necesitas más shots." : "Quizá puedas ahorrar shots."}`
        : "Mide con cualquier N para ver cuánto se dispersan las estimaciones.";
    if (nivel === 2)
      return "El error cae como 1/√N: para dividirlo entre 2 hay que multiplicar N por 4. Compara tu σ con el objetivo y calcula el factor.";
    return `N ≥ p(1−p)/σ² = 0,1875/${fmt(v.tol, 3)}² ≈ ${Math.ceil((P25 * (1 - P25)) / v.tol ** 2)}.`;
  },
  evidencia: ({ res, params }) => ({
    sigmaTeo:
      Math.round(Math.sqrt((P25 * (1 - P25)) / params.shots) * 1e4) / 1e4,
    sigmaObs: Math.round(res.sigmaObs * 1e4) / 1e4,
    media: Math.round(res.media * 1e4) / 1e4,
  }),
  insignias({ params, v }) {
    return params.shots <= 1.1 * Math.ceil((P25 * (1 - P25)) / v.tol ** 2)
      ? ["ahorro"]
      : [];
  },
  trasMedir(ctx) {
    const puntos = (ctx.datos.puntos ?? []).filter(
      ([n]) => n !== ctx.params.shots,
    );
    ctx.datos.puntos = [...puntos, [ctx.params.shots, ctx.res.sigmaObs]].slice(
      -12,
    );
  },
};

// ---------- 3 · Detector de parecidos ----------
const GAMMA = 2;
function rbf(x) {
  const k = (c) => {
    const ps = LUNAS.train.filter((p) => p[2] === c);
    return media(
      ps.map((p) =>
        Math.exp(-GAMMA * ((p[0] - x[0]) ** 2 + (p[1] - x[1]) ** 2)),
      ),
    );
  };
  return k(1) - k(0);
}
const RBF = {
  test: LUNAS.test.map((p) => rbf(p)),
  malla: Array.from({ length: 13 }, (_f, j) =>
    Array.from({ length: 13 }, (_c, i) => rbf([i / 12, j / 12])),
  ),
};
const P = (t) => 20 + t * 320;
const Y = (t) => 340 - t * 320;
const marca = (x, y, clase, extra) =>
  clase === 1
    ? s("polygon", {
        class: `pt c1 ${extra}`,
        points: `${x},${y - 8} ${x + 7},${y + 5} ${x - 7},${y + 5}`,
      })
    : s("circle", { class: `pt c0 ${extra}`, cx: x, cy: y, r: 6 });
const aciertos = (scores) =>
  scores.filter((sc, k) => sc > 0 === (LUNAS.test[k][2] === 1)).length;

const m3 = {
  ayuda: [
    "Clasificar es decidir a qué grupo pertenece un punto. Aquí hay dos grupos: ● y ▲.",
    "Un kernel es un número entre 0 y 1 que dice cuánto se parecen dos puntos: 1 si son iguales.",
    "Cada punto nuevo va al grupo cuyos puntos conocidos se le parecen más en promedio. Una SVM hace algo parecido, pero además aprende un peso para cada punto conocido.",
  ],
  inicial: (copia) => copia?.p ?? { escala: 0.5, reps: 1 },
  objetivo: (v) =>
    `Clasifica bien al menos ${v.meta} de los 8 puntos nuevos con el kernel cuántico.`,
  prediccion: {
    etiqueta: "¿Qué escala de los datos crees que clasificará mejor?",
    opciones: [
      [0.5, "pequeña (≈ 0,5)"],
      [1.5, "media (≈ 1,5)"],
      [4, "grande (≈ 4)"],
    ],
  },
  controles(ctx) {
    const reps = h(
      "fieldset",
      { class: "ctl radios" },
      h("legend", { text: "Capas del feature map (reps):" }),
      [1, 2].map((r) =>
        h(
          "label",
          null,
          h("input", {
            type: "radio",
            name: "reps",
            value: r,
            checked: ctx.params.reps === r,
            onchange: () => ctx.cambiar({ reps: r }),
          }),
          ` ${r}`,
        ),
      ),
    );
    return h(
      "div",
      null,
      deslizador({
        id: "escala",
        etiqueta: "Escala de los datos:",
        min: 0.25,
        max: 5,
        paso: 0.25,
        valor: ctx.params.escala,
        mostrar: (v) => fmt(v, 2),
        alCambiar: (v) => ctx.cambiar({ escala: v }),
      }),
      reps,
    );
  },
  codigo: (p) => codigo.m3(p),
  procesar: (out) => ({
    test: out.test,
    malla: out.malla,
    aciertos: aciertos(out.test),
    contraste: media(out.test.map(Math.abs)),
  }),
  dibujar(vis, ctx) {
    const ver = ctx.datos.ver ?? "q";
    const datos = ver === "rbf" ? RBF : ctx.res;
    const svg = s("svg", {
      viewBox: "0 0 360 360",
      class: "plano",
      role: "img",
      "aria-label": "Plano con los puntos conocidos y los puntos a clasificar",
    });
    svg.append(
      s("rect", { class: "marco", x: 20, y: 20, width: 320, height: 320 }),
    );
    if (datos) {
      const c = 320 / 12;
      datos.malla.forEach((fila, j) =>
        fila.forEach((sc, i) => {
          const x = Math.max(20, P(i / 12) - c / 2);
          const y = Math.max(20, Y(j / 12) - c / 2);
          svg.append(
            s("rect", {
              class: sc > 0 ? "celda c1" : "celda c0",
              x,
              y,
              width: Math.min(340, P(i / 12) + c / 2) - x,
              height: Math.min(340, Y(j / 12) + c / 2) - y,
              "fill-opacity": (
                0.12 +
                0.5 * Math.min(1, Math.abs(sc) / 0.3)
              ).toFixed(2),
            }),
          );
        }),
      );
    }
    for (const [x, y, c] of LUNAS.train)
      svg.append(marca(P(x), Y(y), c, "conocido"));
    LUNAS.test.forEach(([x, y, c], k) => {
      svg.append(marca(P(x), Y(y), c, "nuevo"));
      if (datos) {
        const bien = datos.test[k] > 0 === (c === 1);
        svg.append(
          s("text", {
            class: bien ? "ok" : "mal",
            x: P(x) + 9,
            y: Y(y) - 7,
            text: bien ? "✓" : "✗",
          }),
        );
      }
    });

    const seg = (id, t) =>
      h("button", {
        type: "button",
        class: "seg",
        "aria-pressed": String(ver === id),
        text: t,
        onclick: () => {
          ctx.datos.ver = id;
          m3.dibujar(vis, ctx);
        },
      });
    const resumen = h(
      "div",
      { class: "marcador" },
      datos
        ? [
            h("b", { text: `${aciertos(datos.test)}/8` }),
            h("span", {
              text:
                ver === "rbf"
                  ? `aciertos del RBF clásico (γ = ${GAMMA}), calculado en tu navegador`
                  : `aciertos del kernel cuántico (escala ${fmt(ctx.resParams.escala, 2)}, reps ${ctx.resParams.reps})`,
            }),
          ]
        : h("span", {
            text: "Mide con Qiskit para colorear el plano con lo que predice el kernel.",
          }),
    );
    vis.replaceChildren(
      h(
        "div",
        { class: "segs", role: "group", "aria-label": "Qué kernel ver" },
        seg("q", "Kernel cuántico"),
        seg("rbf", "RBF clásico"),
      ),
      svg,
      h(
        "p",
        { class: "leyenda-plano" },
        "● y ▲: las dos clases · relleno: puntos conocidos · contorno: puntos nuevos · el color del fondo es la clase que predice el kernel",
      ),
      resumen,
    );
  },
  feedback({ res, params, pred }) {
    const e = params.escala;
    const regimen =
      e < 0.75
        ? "Con escala pequeña todos los estados se parecen (k ≈ 1): el contraste entre clases es bajo y la frontera queda borrosa."
        : e > 2.5
          ? "Con escala grande el kernel oscila: puntos lejanos pueden parecer similares y aparecen islas de color."
          : "Con una escala intermedia, los puntos cercanos se parecen y los lejanos no: la frontera sigue la forma de las lunas.";
    return [
      pred == null
        ? null
        : `Predijiste una escala ${pred === 0.5 ? "pequeña" : pred === 1.5 ? "media" : "grande"}.`,
      `Con escala ${fmt(e, 2)} y reps = ${params.reps}, el kernel cuántico acierta ${res.aciertos} de 8 (contraste medio ${fmt(res.contraste, 3)}).`,
      regimen,
      params.reps === 2
        ? "Con reps = 2 el estado da más vueltas: más capas no siempre ayudan."
        : null,
      `Para comparar: el RBF clásico con γ = ${GAMMA} acierta ${aciertos(RBF.test)} de 8 en estos mismos datos. Usar un circuito no da ventaja por sí solo.`,
    ];
  },
  evaluar({ res, v }) {
    return res.aciertos >= v.meta
      ? {
          ok: true,
          texto: `${res.aciertos} de 8 aciertos con el kernel cuántico (meta: ${v.meta}).`,
        }
      : {
          ok: false,
          texto: `${res.aciertos} de 8 aciertos; la meta es ${v.meta}. Cambia la escala y vuelve a medir.`,
        };
  },
  pista({ res, params }, nivel) {
    if (nivel === 1) {
      if (!res)
        return "Mide con la escala que predijiste y mira cuántos ✓ salen.";
      if (params.reps === 2)
        return "Con reps = 2 ninguna escala llega a 7 de 8 en estos datos. Vuelve a reps = 1.";
      return params.escala < 0.75
        ? "El fondo es casi uniforme: todos los puntos se parecen demasiado. Aumenta la escala."
        : params.escala > 2.5
          ? "Hay islas de color: el kernel oscila. Disminuye la escala."
          : "Vas bien: prueba escalas vecinas, de 0,25 en 0,25.";
    }
    if (nivel === 2)
      return "La escala hace el papel de γ en el RBF: multiplica los datos antes de rotar los qubits. Muy pequeña, todo se parece; muy grande, el parecido oscila.";
    return "Prueba escalas entre 1,25 y 1,75 con reps = 1.";
  },
  evidencia: ({ res }) => ({
    aciertos: res.aciertos,
    contraste: Math.round(res.contraste * 1e4) / 1e4,
  }),
  insignias: ({ res }) => (res.aciertos === 8 ? ["ajuste-fino"] : []),
};

// ---------- Reto · El kernel con ruido ----------
const Z95 = 1.645;
const fiabilidad = (ka, kb, n) =>
  phi((ka - kb) / Math.sqrt((ka * (1 - ka) + kb * (1 - kb)) / n));

const t1 = {
  ayuda: [
    "En un computador cuántico real el kernel no se calcula exacto: se prepara U(x), se deshace U(x′) y se cuenta cuántas veces sale 00. Es Monte Carlo otra vez.",
    "El punto a clasificar pertenece a la clase A. Se clasifica bien si su parecido estimado con A supera al estimado con B.",
    "Fiabilidad: el porcentaje de veces que la clasificación sale bien si repites el experimento.",
  ],
  inicial: (copia) => copia?.p ?? { shots: 50, reps: 20 },
  objetivo: (v) =>
    `Elige los shots por estimación para clasificar bien el punto al menos el 95 % de las veces, con un presupuesto de ${v.presupuesto}.`,
  prediccion: {
    etiqueta: "¿Cuántos shots por estimación crees que necesitas?",
    min: 1,
    max: 5000,
  },
  controles(ctx) {
    return deslizador({
      id: "shots-t",
      etiqueta: "Shots por estimación N:",
      min: 10,
      max: 500,
      paso: 10,
      valor: ctx.params.shots,
      mostrar: String,
      alCambiar: (v) => ctx.cambiar({ shots: v }),
    });
  },
  codigo: (p) => codigo.t1(p),
  procesar: (out, p) => ({
    ...out,
    aciertos: out.pa.filter((a, i) => a > out.pb[i]).length,
    fiab: fiabilidad(out.ka, out.kb, p.shots),
  }),
  dibujar(vis, ctx) {
    const { res } = ctx;
    const W = 520;
    const X = (k) => 120 + ((k - 0.3) / 0.5) * (W - 150);
    const svg = s("svg", {
      viewBox: `0 0 ${W} 150`,
      class: "grafico",
      role: "img",
      "aria-label": "Estimaciones del kernel con cada clase",
    });
    const fila = (y, t, ps, k) => {
      svg.append(s("text", { class: "nota", x: 8, y: y + 4, text: t }));
      svg.append(
        s("line", { class: "eje tenue", x1: 120, x2: W - 30, y1: y, y2: y }),
      );
      if (!res) return;
      ps.forEach((p, i) =>
        svg.append(
          s("circle", {
            class: "punto",
            cx: X(Math.min(0.8, Math.max(0.3, p))),
            cy: y - 8 + (i % 4) * 5,
            r: 4,
          }),
        ),
      );
      svg.append(
        s("line", {
          class: "real",
          x1: X(k),
          x2: X(k),
          y1: y - 16,
          y2: y + 14,
        }),
      );
    };
    fila(36, "parecido con A ✓", res?.pa, res?.ka);
    fila(86, "parecido con B", res?.pb, res?.kb);
    ejeX(svg, 120, W - 30, 116, [0.3, 0.4, 0.5, 0.6, 0.7, 0.8], X, (t) =>
      fmt(t, 1),
    );
    const pastillas = h(
      "ol",
      { class: "pastillas", "aria-label": "Resultado de cada repetición" },
      res
        ? res.pa.map((a, i) =>
            h("li", {
              class: a > res.pb[i] ? "ok" : "mal",
              text: a > res.pb[i] ? "✓" : "✗",
              title: `Repetición ${i + 1}`,
            }),
          )
        : null,
    );
    vis.replaceChildren(
      h("p", {
        class: "vis-t",
        text: "20 estimaciones de cada kernel (puntos) y su valor exacto (línea)",
      }),
      svg,
      h("p", {
        class: "vis-t",
        text: res
          ? `Clasificación en cada repetición: ${res.aciertos} de 20 bien`
          : "Clasificación en cada repetición",
      }),
      pastillas,
    );
  },
  feedback({ res, params, pred }) {
    const sa = Math.sqrt((res.ka * (1 - res.ka)) / params.shots);
    const sd = Math.sqrt(
      (res.ka * (1 - res.ka) + res.kb * (1 - res.kb)) / params.shots,
    );
    return [
      pred == null ? null : `Tu predicción: ${pred} shots.`,
      `Kernels exactos (Statevector): k_A = ${fmt(res.ka, 3)}, k_B = ${fmt(res.kb, 3)}. La diferencia es solo Δ = ${fmt(res.ka - res.kb, 3)}.`,
      `Con N = ${params.shots}, cada estimación se equivoca ≈ ${fmt(sa, 3)} y la diferencia estimada, σ_Δ = ${fmt(sd, 3)}.`,
      `Fiabilidad teórica Φ(Δ/σ_Δ) = ${pct(res.fiab, 1)}. En estas 20 repeticiones simuladas acertó ${res.aciertos}.`,
      "En hardware real se sumaría el ruido del dispositivo; aquí solo se simula el muestreo.",
    ];
  },
  evaluar({ res, params, v }) {
    if (params.shots > v.presupuesto)
      return { ok: false, texto: `N = ${params.shots} pasa del presupuesto.` };
    return res.fiab >= 0.95
      ? {
          ok: true,
          texto: `Fiabilidad teórica ${pct(res.fiab, 1)} ≥ 95 % con ${params.shots} shots por estimación.`,
        }
      : {
          ok: false,
          texto: `Fiabilidad teórica ${pct(res.fiab, 1)}: no llega al 95 %.`,
        };
  },
  pista({ res, params }, nivel) {
    if (nivel === 1)
      return res
        ? `Es el error de «Cazar el ruido»: cada estimación tiene σ = √(k(1−k)/N). Con N = ${params.shots}, el ruido de la diferencia (${fmt(Math.sqrt((res.ka * (1 - res.ka) + res.kb * (1 - res.kb)) / params.shots), 3)}) frente a Δ = ${fmt(res.ka - res.kb, 3)}.`
        : "Mide con cualquier N: verás los kernels exactos y cuánto se mezclan las dos nubes.";
    if (nivel === 2)
      return `Para acertar el 95 %, Δ debe ser al menos ${fmt(Z95, 2)}·σ_Δ, con σ_Δ = √((k_A(1−k_A) + k_B(1−k_B))/N).`;
    const ka = res?.ka ?? 0.558;
    const kb = res?.kb ?? 0.478;
    return `N ≥ (${fmt(Z95, 2)}/Δ)²·(k_A(1−k_A) + k_B(1−k_B)) ≈ ${Math.ceil((Z95 / (ka - kb)) ** 2 * (ka * (1 - ka) + kb * (1 - kb)))}.`;
  },
  evidencia: ({ res }) => ({
    ka: Math.round(res.ka * 1e4) / 1e4,
    kb: Math.round(res.kb * 1e4) / 1e4,
    fiab: Math.round(res.fiab * 1e3) / 1e3,
    aciertos: res.aciertos,
  }),
  insignias: () => ["puente"],
};

export const SPECS = { m1, m2, m3, t1 };

// ---------- el ciclo común ----------
const paso = (n, t) => h("li", { "data-paso": n, text: t });
// La semilla cambia sola tras cada medida: no cuenta como un cambio del jugador.
const sinSemilla = ({ seed: _seed, ...resto }) => JSON.stringify(resto);
const linea = (i, k, ...c) =>
  h(
    "li",
    { style: `--i:${i}` },
    h("span", { class: "k", text: k }),
    h("div", null, ...c),
  );

export function abrirMision(
  raiz,
  m,
  { st, guardarSt, copia, irA, alCambiarProgreso },
) {
  const spec = SPECS[m.id];
  const datos = copia ? {} : datosMision(st, m.id);
  if (!copia && !datos.inicio) {
    datos.inicio = true;
    guardarSt();
  }
  const vi0 = copia
    ? copia.v
    : Math.max(
        0,
        m.variantes.findIndex(
          (_, i) => !st.evidencias.some((e) => e.id === `${m.id}:${i}`),
        ),
      );
  const ctx = {
    m,
    vi: vi0,
    v: m.variantes[vi0],
    params: parametrosDemo(m.id, spec.inicial(copia)),
    res: null,
    resParams: null,
    pred: copia?.pred ?? null,
    datos,
    nivelPista: 0,
    pistasUsadas: 0,
    cambiar(p) {
      Object.assign(ctx.params, p);
      ctx.aviso = null;
      if (m.id === "m1") spec.dibujar(vis, ctx);
      pintarCodigo();
      pintarEstado();
    },
  };

  const pasos = h(
    "ol",
    { class: "pasos", "aria-label": "Progreso de la misión" },
    paso(1, "Predice"),
    paso(2, "Experimenta"),
    paso(3, "Observa"),
    paso(4, "Demuestra"),
  );

  const selVariante = h(
    "select",
    {
      id: "variante",
      onchange: (e) => {
        ctx.vi = Number(e.target.value);
        ctx.v = m.variantes[ctx.vi];
        objetivoTxt.textContent = spec.objetivo(ctx.v);
        resultadoReto.replaceChildren();
        spec.dibujar(vis, ctx);
        pintarEstado();
      },
    },
    m.variantes.map((v, i) =>
      h(
        "option",
        { value: i, selected: i === ctx.vi },
        `${v.nombre}${st.evidencias.some((e) => e.id === `${m.id}:${i}`) ? " ✓" : ""}`,
      ),
    ),
  );
  const objetivoTxt = h("p", { class: "obj-txt", text: spec.objetivo(ctx.v) });

  const predInput = spec.prediccion.opciones
    ? h(
        "fieldset",
        { class: "ctl radios pred" },
        h("legend", { text: spec.prediccion.etiqueta }),
        spec.prediccion.opciones.map(([val, t]) =>
          h(
            "label",
            null,
            h("input", {
              type: "radio",
              name: "pred",
              value: val,
              checked: ctx.pred === val,
              onchange: () => {
                ctx.pred = val;
                pintarEstado();
              },
            }),
            ` ${t}`,
          ),
        ),
      )
    : h(
        "div",
        { class: "ctl pred" },
        h("label", { for: "pred", text: spec.prediccion.etiqueta }),
        h("input", {
          id: "pred",
          type: "number",
          inputmode: "numeric",
          min: spec.prediccion.min,
          max: spec.prediccion.max,
          value: ctx.pred ?? "",
          placeholder: "Tu predicción",
          oninput: (e) => {
            const n = Number(e.target.value);
            ctx.pred =
              e.target.value.trim() === "" || !Number.isFinite(n) ? null : n;
            pintarEstado();
          },
        }),
      );

  const btnMedir = h(
    "button",
    { type: "button", class: "primario", onclick: () => medir() },
    DEMO_MODE ? "Ver resultado de ejemplo" : "Medir con Qiskit",
  );
  const estadoRun = h("p", {
    class: "estado-run",
    role: "status",
    "aria-live": "polite",
  });
  const btnPista = h(
    "button",
    { type: "button", class: "secundario", onclick: () => pedirPista() },
    "Pedir una pista",
  );
  const pistas = h("ol", { class: "pistas", "aria-live": "polite" });
  const btnReto = h(
    "button",
    { type: "button", class: "reto", onclick: () => comprobar() },
    "Comprobar el reto",
  );
  const resultadoReto = h("div", {
    class: "resultado-reto",
    role: "status",
    "aria-live": "polite",
  });
  const vis = h("div", { class: "vis" });
  const fb = h("div", { class: "feedback", "aria-live": "polite" });
  const codigoPre = h("code");
  const btnCopiar = h(
    "button",
    {
      type: "button",
      class: "secundario",
      onclick: (e) => copiar(spec.codigo(ctx.params), e.currentTarget),
    },
    "Copiar código",
  );

  function pintarCodigo() {
    codigoPre.textContent = spec.codigo(ctx.params);
  }

  const desactualizado = () =>
    ctx.res && sinSemilla(ctx.resParams) !== sinSemilla(ctx.params);

  function pintarEstado() {
    const pasado =
      !copia && st.evidencias.some((e) => e.id === `${m.id}:${ctx.vi}`);
    const hecho = {
      1: ctx.pred != null,
      2: !!ctx.res,
      3: !!ctx.res,
      4: pasado,
    };
    const actual = !hecho[1] ? 1 : !hecho[2] ? 2 : !hecho[4] ? 4 : 0;
    for (const li of pasos.children) {
      const n = Number(li.dataset.paso);
      li.className = hecho[n] ? "hecho" : "";
      if (n === actual) li.setAttribute("aria-current", "step");
      else li.removeAttribute("aria-current");
    }
    const sinPred = ctx.pred == null && !ctx.res;
    btnMedir.disabled = ctx.corriendo || sinPred;
    btnMedir.title = sinPred ? "Anota tu predicción primero" : "";
    btnReto.disabled = ctx.corriendo || !ctx.res || desactualizado();
    estadoRun.classList.toggle("error", !!ctx.aviso?.error);
    estadoRun.textContent = ctx.corriendo
      ? DEMO_MODE
        ? "Cargando resultado precomputado…"
        : "Ejecutando en el simulador de Qiskit…"
      : ctx.aviso?.error
        ? ctx.aviso.texto
        : sinPred
          ? "Primero apuesta: anota tu predicción."
          : desactualizado()
            ? "Cambiaste los valores: vuelve a medir para comprobar el reto con ellos."
            : ctx.aviso
              ? ctx.aviso.texto
              : ctx.res
                ? ""
                : "Listo para medir.";
  }

  async function medir() {
    ctx.corriendo = true;
    ctx.aviso = null;
    btnMedir.textContent = DEMO_MODE ? "Cargando…" : "Midiendo…";
    pintarEstado();
    const params = { ...ctx.params };
    try {
      const out = await medirMision(m.id, params);
      ctx.res = spec.procesar(out, params);
      ctx.resParams = params;
      ctx.animado = false;
      spec.trasMedir?.(ctx);
      if (!copia) {
        const nuevos = [];
        if (
          ctx.pred != null &&
          premiar(st, `${m.id}:prediccion`, XP.prediccion)
        )
          nuevos.push(`+${XP.prediccion} XP por tu primera predicción`);
        if (premiar(st, `${m.id}:experimento`, XP.experimento))
          nuevos.push(`+${XP.experimento} XP por tu primer experimento`);
        if (darInsignia(st, "primera-medida"))
          nuevos.push("Insignia «Primera medida»");
        datos.corrio = true;
        guardarSt();
        alCambiarProgreso?.();
        if (nuevos.length) ctx.aviso = { texto: nuevos.join(" · ") };
      }
      spec.dibujar(vis, ctx);
      fb.replaceChildren(
        h("h3", { text: "Qué significa" }),
        h(
          "ul",
          null,
          spec
            .feedback(ctx)
            .filter(Boolean)
            .map((t) => {
              const li = h("li");
              li.append(textoConMath(t));
              return li;
            }),
        ),
      );
      resultadoReto.replaceChildren();
    } catch (e) {
      ctx.aviso = { texto: e.message, error: true };
    } finally {
      ctx.corriendo = false;
      btnMedir.textContent = DEMO_MODE
        ? ctx.res
          ? "Consultar de nuevo"
          : "Ver resultado de ejemplo"
        : ctx.res
          ? "Volver a medir"
          : "Medir con Qiskit";
      pintarCodigo();
      pintarEstado();
    }
  }

  function pedirPista() {
    ctx.nivelPista = Math.min(3, ctx.nivelPista + 1);
    ctx.pistasUsadas = Math.max(ctx.pistasUsadas, ctx.nivelPista);
    pistas.append(h("li", { text: spec.pista(ctx, ctx.nivelPista) }));
    if (ctx.nivelPista === 3) {
      btnPista.disabled = true;
      btnPista.textContent = "No hay más pistas";
    } else btnPista.textContent = `Otra pista (${ctx.nivelPista}/3)`;
  }

  function comprobar() {
    const r = spec.evaluar({ ...ctx, params: ctx.resParams });
    if (!r.ok) {
      resultadoReto.replaceChildren(
        h("p", { class: "mal" }, h("b", { text: "Todavía no. " }), r.texto),
        h("p", {
          class: "sugerencia",
          text:
            ctx.nivelPista < 3
              ? "Puedes intentarlo cuantas veces quieras. Si te atascas, pide una pista."
              : "Puedes intentarlo cuantas veces quieras.",
        }),
      );
      return;
    }
    if (copia) {
      resultadoReto.replaceChildren(
        h(
          "p",
          { class: "bien" },
          h("b", { text: "Superado en la copia. " }),
          r.texto,
          " Una copia de exploración no guarda evidencias ni recompensas.",
        ),
      );
      return;
    }
    const antes = new Set(
      MISIONES.filter((x) => desbloqueada(st, x)).map((x) => x.id),
    );
    const ev = {
      m: m.id,
      demo: DEMO_MODE,
      v: ctx.vi,
      h: ctx.pistasUsadas,
      pred: ctx.pred,
      p: ctx.resParams,
      r: spec.evidencia(ctx),
    };
    const reg = registrarExito(st, ev);
    const insignias = reg.nueva
      ? [
          ...spec.insignias(ctx),
          ...(ctx.pistasUsadas === 0 ? ["sin-pistas"] : []),
        ].filter((id) => darInsignia(st, id))
      : [];
    guardarSt();
    alCambiarProgreso?.({ destacar: m.demuestra[0] });
    const abiertas = MISIONES.filter(
      (x) => desbloqueada(st, x) && !antes.has(x.id),
    );
    resultadoReto.replaceChildren(
      h("p", { class: "bien" }, h("b", { text: "¡Reto superado! " }), r.texto),
    );
    for (const o of selVariante.options) {
      const i = Number(o.value);
      o.textContent = `${m.variantes[i].nombre}${st.evidencias.some((e) => e.id === `${m.id}:${i}`) ? " ✓" : ""}`;
    }
    pintarEstado();
    celebrar({
      m,
      r,
      reg,
      insignias,
      abiertas,
      ev: st.evidencias.find((e) => e.id === `${m.id}:${ctx.vi}`),
      st,
      irA,
    });
    ctx.nivelPista = 0;
    ctx.pistasUsadas = 0;
    pistas.replaceChildren();
    btnPista.disabled = false;
    btnPista.textContent = "Pedir una pista";
  }

  raiz.replaceChildren(
    h(
      "article",
      { class: `mision${copia ? " copia" : ""}` },
      h(
        "header",
        { class: "mis-cab" },
        h("a", { class: "volver", href: "#mapa", text: "← Mapa" }),
        h("p", {
          class: "kicker",
          text: `${m.reto ? "Reto de transferencia" : "Misión"} · ${m.puente}`,
        }),
        h("h1", { text: m.titulo }),
        h(
          "p",
          { class: "backend" },
          h("span", {
            class: "chip-sim",
            text: DEMO_MODE ? "Demo interactiva" : "Simulador",
          }),
          DEMO_MODE
            ? " Resultados precomputados con Qiskit para cada valor de los controles. Puedes predecir, explorar, superar retos y ver el portafolio de demostración. No se ejecuta código aquí; al repetir una configuración verás el mismo resultado."
            : " StatevectorSampler de Qiskit, sin hardware cuántico. Las probabilidades teóricas salen de Statevector; las frecuencias, de muestrear shots.",
        ),
        copia
          ? h("p", {
              class: "aviso-copia",
              text: "Copia de exploración de una evidencia: puedes cambiar todo; la evidencia original no se modifica y aquí no se gana nada.",
            })
          : null,
      ),
      h(
        "section",
        { class: "objetivo" },
        h(
          "div",
          { class: "obj-cab" },
          h("h2", { text: "Objetivo" }),
          h("label", { class: "var" }, "Configuración ", selVariante),
        ),
        objetivoTxt,
        h(
          "p",
          { class: "decide" },
          h("b", { text: "Tú decides: " }),
          m.diseno.decision,
        ),
        h(
          "details",
          { class: "ayuda" },
          h("summary", { text: "¿Necesitas un repaso rápido? (30 s)" }),
          h(
            "ul",
            null,
            spec.ayuda.map((t) => h("li", { text: t })),
          ),
        ),
      ),
      pasos,
      h(
        "div",
        { class: "area" },
        h(
          "section",
          { class: "panel-ctl", "aria-label": "Controles" },
          predInput,
          spec.controles(ctx),
          h("div", { class: "acciones" }, btnMedir),
          estadoRun,
          h("div", { class: "pista-caja" }, btnPista, pistas),
          h("div", { class: "reto-caja" }, btnReto, resultadoReto),
        ),
        h(
          "section",
          { class: "panel-vis", "aria-label": "Resultado del experimento" },
          vis,
          fb,
        ),
      ),
      h(
        "details",
        { class: "codigo" },
        h("summary", { text: "Ver el código Qiskit de este experimento" }),
        h("pre", null, codigoPre),
        btnCopiar,
      ),
    ),
  );
  spec.dibujar(vis, ctx);
  pintarCodigo();
  pintarEstado();
}

// Cierre breve: resultado, logro, mapa actualizado y nueva posibilidad. Todo aparece a la vez
// para quien no quiera esperar; el movimiento solo escalona la entrada.
function celebrar({ m, r, reg, insignias, abiertas, ev, st, irA }) {
  const dlg = h("dialog", { class: "logro", "aria-labelledby": "logro-t" });
  const restantes = m.variantes.filter(
    (_, i) => !st.evidencias.some((e) => e.id === `${m.id}:${i}`),
  );
  if (DEMO_MODE)
    dlg.append(
      h("p", {
        class: "aviso",
        text: "Progreso de demostración con resultados precomputados de Qiskit.",
      }),
    );
  dlg.append(
    h("h2", {
      id: "logro-t",
      text: reg.nueva ? `¡${m.titulo}: superada!` : "Superado otra vez",
    }),
    h(
      "ol",
      null,
      linea(0, "Resultado", r.texto),
      linea(
        1,
        "Logro",
        reg.nueva
          ? `Demostraste ${m.demuestra.map((id) => `«${habilidad(id).nombre}»`).join(" y ")}. +${reg.xp} XP de actividad.`
          : "Ya tenías la evidencia de esta configuración: no suma XP otra vez.",
        insignias.length
          ? h(
              "p",
              { class: "ins" },
              `Insignia nueva: ${insignias.map((id) => `«${INSIGNIAS.find((x) => x.id === id).nombre}»`).join(", ")}`,
            )
          : null,
      ),
      linea(
        2,
        "Mapa",
        `${m.demuestra.map((id) => habilidad(id).corto).join(" y ")} ${m.demuestra.length > 1 ? "brillan" : "brilla"} ahora como ★ demostrada${m.demuestra.length > 1 ? "s" : ""}.`,
      ),
      linea(
        3,
        "Nueva posibilidad",
        abiertas.length
          ? `Desbloqueaste ${abiertas.map((x) => `«${x.titulo}»`).join(" y ")}.${abiertas.length > 1 ? " Elige por cuál seguir." : ""}`
          : restantes.length
            ? `Puedes repetirla con otra configuración: ${restantes[0].nombre}.`
            : m.id === "t1"
              ? "Completaste la ruta. El nivel 3 (gradientes ↔ parameter-shift) está en preparación."
              : "Completa la otra misión para abrir el reto de transferencia.",
      ),
    ),
    h(
      "div",
      { class: "logro-acc" },
      h(
        "button",
        {
          type: "button",
          class: "primario",
          onclick: () => {
            dlg.close();
            irA("#mapa", { destacar: m.demuestra[0] });
          },
        },
        "Ver el mapa",
      ),
      ev
        ? h(
            "button",
            {
              type: "button",
              class: "secundario",
              onclick: () => {
                dlg.close();
                irA(`#portafolio`, { evidencia: ev.id });
              },
            },
            "Ver la evidencia",
          )
        : null,
      h(
        "button",
        { type: "button", class: "secundario", onclick: () => dlg.close() },
        "Seguir aquí",
      ),
    ),
  );
  dlg.addEventListener("close", () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
}

// Ficha de una evidencia: la usan el mapa, el portafolio y la vista pública.
export function fichaEvidencia(e, { publica = false, alCompartir } = {}) {
  const d = describir(e);
  return h(
    "div",
    { class: "ficha" },
    h("p", {
      class: "kicker",
      text: `${d.mision.reto ? "Reto de transferencia" : "Misión"} · ${d.mision.titulo} · ${d.fecha}`,
    }),
    h("h3", { text: d.titulo }),
    h(
      "dl",
      null,
      h("dt", { text: "Problema" }),
      h("dd", { text: d.problema }),
      h("dt", { text: "Qué hizo" }),
      h("dd", { text: `${d.hizo} ${d.ayuda}` }),
      h("dt", { text: "Conceptos" }),
      h("dd", { text: d.conceptos.join(" · ") }),
      h("dt", { text: "Resultado" }),
      h("dd", { text: d.resultado }),
      h("dt", { text: "Ejecución" }),
      h("dd", { text: d.ejecucion }),
    ),
    h(
      "details",
      { class: "codigo" },
      h("summary", { text: "Cómo reproducirlo: código Qiskit" }),
      h("pre", null, h("code", { text: d.codigo })),
      h(
        "button",
        {
          type: "button",
          class: "secundario",
          onclick: (ev) => copiar(d.codigo, ev.currentTarget),
        },
        "Copiar código",
      ),
    ),
    h(
      "div",
      { class: "ficha-acc" },
      h(
        "a",
        {
          class: "secundario boton",
          href: `#copia=${encodeURIComponent(JSON.stringify({ m: e.m, v: e.v, p: e.p, pred: e.pred }))}`,
        },
        "Explorar una copia",
      ),
      !publica && alCompartir
        ? h(
            "button",
            {
              type: "button",
              class: "secundario",
              onclick: (ev) => alCompartir(e, ev.currentTarget),
            },
            "Compartir esta evidencia",
          )
        : null,
    ),
  );
}
