// Bloques interactivos: el alumno los maneja con clic (y con el teclado) durante la narración o al
// terminarla. Se cargan después de blocks.js y se enchufan igual, mediante window.BLOCKS.
//
//   lab       taller de circuitos: puertas que se ponen y se quitan con clic, ángulos con
//             deslizador y probabilidades en vivo (vector de estado exacto, calculado aquí)
//   slider    deslizador que mueve un parámetro de otro bloque (plot, lab, shots, kernelmap)
//   shots     máquina de muestreo: cada botón saca N muestras y la gráfica muestra el error
//   kernelmap similitud con un punto elegido con clic: kernel RBF y kernel cuántico ZZ
//
// Cada bloque interactivo lleva la clase .live y avisa de cada cambio con A.changed(o). Para las
// actividades (ask kind 'task') ofrece check(goal), que dice si se cumplió la meta, y status(),
// una línea con lo que lleva hecho el alumno.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  "use strict";
  const B = window.BLOCKS;
  const { PI, SQRT1_2: SQ, cos, sin, sqrt } = Math;

  // ---------------------------------------------------------------- vector de estado
  // Amplitudes en dos Float64Array (real e imaginaria). El índice i tiene el qubit q en el bit q:
  // la etiqueta de i se escribe q_{n-1}…q_0, como en Qiskit.
  const phase = (t) => [1, 0, 0, 0, 0, 0, cos(t), sin(t)];
  // Matrices 2×2 como [a, b, c, d] aplanadas en pares (re, im).
  const M1 = {
    id: () => [1, 0, 0, 0, 0, 0, 1, 0],
    h: () => [SQ, 0, SQ, 0, SQ, 0, -SQ, 0],
    x: () => [0, 0, 1, 0, 1, 0, 0, 0],
    y: () => [0, 0, 0, -1, 0, 1, 0, 0],
    z: () => phase(PI),
    s: () => phase(PI / 2),
    sdg: () => phase(-PI / 2),
    t: () => phase(PI / 4),
    tdg: () => phase(-PI / 4),
    p: phase,
    sx: () => [0.5, 0.5, 0.5, -0.5, 0.5, -0.5, 0.5, 0.5],
    rx: (t) => [cos(t / 2), 0, 0, -sin(t / 2), 0, -sin(t / 2), cos(t / 2), 0],
    ry: (t) => [cos(t / 2), 0, -sin(t / 2), 0, sin(t / 2), 0, cos(t / 2), 0],
    rz: (t) => [cos(t / 2), -sin(t / 2), 0, 0, 0, 0, cos(t / 2), sin(t / 2)],
  };
  const TWO = new Set(["cx", "cz", "swap", "cp"]);

  function zero(n) {
    const re = new Float64Array(1 << n),
      im = new Float64Array(1 << n);
    re[0] = 1;
    return { n, re, im };
  }
  function apply1(st, q, m) {
    const { re, im } = st,
      b = 1 << q;
    for (let i = 0; i < re.length; i++) {
      if (i & b) continue;
      const j = i | b,
        ar = re[i],
        ai = im[i],
        br = re[j],
        bi = im[j];
      re[i] = m[0] * ar - m[1] * ai + m[2] * br - m[3] * bi;
      im[i] = m[0] * ai + m[1] * ar + m[2] * bi + m[3] * br;
      re[j] = m[4] * ar - m[5] * ai + m[6] * br - m[7] * bi;
      im[j] = m[4] * ai + m[5] * ar + m[6] * bi + m[7] * br;
    }
  }
  function swapAmp(st, i, j) {
    [st.re[i], st.re[j]] = [st.re[j], st.re[i]];
    [st.im[i], st.im[j]] = [st.im[j], st.im[i]];
  }
  // Aplica una operación {g, q, theta?} (theta: ángulo ya resuelto). measure y barrier no cambian el
  // estado: las probabilidades son las de antes de medir, como en las vistas de Composer.
  function applyOp(st, op, theta) {
    const [a, b] = op.q;
    if (op.g === "cx") {
      for (let i = 0; i < st.re.length; i++)
        if (i & (1 << a) && !(i & (1 << b))) swapAmp(st, i, i | (1 << b));
    } else if (op.g === "cz" || op.g === "cp") {
      const [c, s] = op.g === "cz" ? [-1, 0] : [cos(theta), sin(theta)];
      for (let i = 0; i < st.re.length; i++)
        if (i & (1 << a) && i & (1 << b)) {
          const r = st.re[i],
            m = st.im[i];
          st.re[i] = c * r - s * m;
          st.im[i] = c * m + s * r;
        }
    } else if (op.g === "swap") {
      for (let i = 0; i < st.re.length; i++)
        if (i & (1 << a) && !(i & (1 << b)))
          swapAmp(st, i, i ^ (1 << a) ^ (1 << b));
    } else if (M1[op.g]) apply1(st, a, M1[op.g](theta));
  }
  const probsOf = (st) => [...st.re].map((r, i) => r * r + st.im[i] ** 2);
  const bits = (i, n) => i.toString(2).padStart(n, "0");

  // ---------------------------------------------------------------- formato
  // Un ángulo como fracción de π si lo es (π/3, 2π/3, −π/2) y, si no, con dos decimales.
  function fmtAngle(v) {
    const r = v / PI;
    for (const d of [1, 2, 3, 4, 6, 8, 12, 24]) {
      const k = Math.round(r * d);
      if (Math.abs(k / d - r) > 1e-6) continue;
      if (k === 0) return "0";
      const sign = k < 0 ? "−" : "",
        num = Math.abs(k) === 1 ? "π" : `${Math.abs(k)}π`;
      return d === 1 ? sign + num : `${sign}${num}/${d}`;
    }
    return v.toFixed(2).replace("-", "−");
  }
  const NICE = [
    [1, ""],
    [SQ, "\\tfrac{1}{\\sqrt2}"],
    [0.5, "\\tfrac12"],
    [SQ / 2, "\\tfrac{1}{2\\sqrt2}"],
    [sqrt(3) / 2, "\\tfrac{\\sqrt3}{2}"],
  ];
  const mag = (v) => {
    const hit = NICE.find(([x]) => Math.abs(v - x) < 1e-6);
    return hit ? hit[1] : v.toFixed(2);
  };
  // |ψ⟩ en LaTeX: solo los términos con amplitud no nula.
  function ketTex(st) {
    const terms = [];
    for (let i = 0; i < st.re.length; i++) {
      const r = st.re[i],
        m = st.im[i];
      if (r * r + m * m < 1e-12) continue;
      const k = `|${bits(i, st.n)}\\rangle`;
      let c, neg;
      if (Math.abs(m) < 1e-9) [c, neg] = [mag(Math.abs(r)), r < 0];
      else if (Math.abs(r) < 1e-9) {
        const s = mag(Math.abs(m));
        [c, neg] = [s ? `${s}\\,i` : "i", m < 0];
      } else {
        [c, neg] = [
          `(${r.toFixed(2)}${m < 0 ? "-" : "+"}${Math.abs(m).toFixed(2)}i)`,
          false,
        ];
      }
      terms.push((neg ? "-" : terms.length ? "+" : "") + c + k);
    }
    return "|\\psi\\rangle=" + terms.join("");
  }

  // ---------------------------------------------------------------- piezas comunes
  // Deslizador con etiqueta y valor. cfg: label, min, max, step, value, fmt ('pi' o 'num'), digits.
  function makeSlider(parent, A, cfg, onInput) {
    const wrap = A.el("label", "lslider", parent);
    A.rich(A.el("span", "lname", wrap), cfg.label || "");
    const inp = A.el("input", "", wrap);
    Object.assign(inp, {
      type: "range",
      min: cfg.min ?? 0,
      max: cfg.max ?? 1,
      step: cfg.step ?? 0.01,
    });
    const out = A.el("output", "lval", wrap);
    const show = (v) =>
      (out.textContent =
        cfg.fmt === "pi" ? fmtAngle(v) : v.toFixed(cfg.digits ?? 2));
    const set = (v) => {
      inp.value = v;
      show(+inp.value);
    };
    inp.addEventListener("input", () => {
      show(+inp.value);
      onInput(+inp.value);
    });
    set(cfg.value ?? cfg.min ?? 0);
    return { set, input: inp };
  }
  const NAME = {
    sdg: "S†",
    tdg: "T†",
    sx: "√X",
    cx: "CX",
    cz: "CZ",
    swap: "SWAP",
  };
  const PCOL = {
    h: "red",
    x: "blue",
    y: "blue",
    z: "blue",
    cx: "blue",
    cz: "blue",
    swap: "blue",
    s: "violet",
    sdg: "violet",
    t: "violet",
    tdg: "violet",
    rx: "teal",
    ry: "teal",
    rz: "teal",
  };
  const sub = (i) => "₀₁₂₃₄₅₆₇₈₉"[i];

  // ---------------------------------------------------------------- taller de circuitos
  // s: qubits, ops (G(...); fixed=True impide quitarla; theta='θ' toma el ángulo de params),
  //    gates (paleta; sin paleta el circuito no se edita), params {nombre: {label, min, max,
  //    step, value, fmt}}, ket (muestra |ψ⟩), maxops.
  // Metas: {probs: {'00': 0.5, '11': 0.5}, tol}: las demás etiquetas deben quedar en 0.
  B.lab = (box, s, A) => {
    const n = s.qubits,
      P = {},
      base = structuredClone(s.ops || []);
    for (const [k, c] of Object.entries(s.params || {})) P[k] = c.value ?? 0;
    let ops = structuredClone(base),
      sel = null,
      ctrl = null;
    const o = { spec: s, P };
    box.classList.add("live");
    const grid = A.el("div", "lab-grid", box);
    const left = A.el("div", "lab-left", grid),
      right = A.el("div", "lab-right", grid);
    const editable = !!(s.gates && s.gates.length);
    const pal = editable ? A.el("div", "lab-pal", left) : null;
    const circBox = A.el("div", "fig circuit lab-circ", left);
    const hint = A.el("div", "lab-hint", left);
    const histBox = A.el("div", "fig hist", right);
    const ketBox = s.ket ? A.el("div", "lab-ket", right) : null;
    const sliders = {};
    if (s.params) {
      const sl = A.el("div", "lab-sliders", box);
      for (const [k, c] of Object.entries(s.params))
        sliders[k] = makeSlider(sl, A, { label: k, ...c }, (v) => {
          P[k] = v;
          render(true);
        });
    }
    const theta = (op) =>
      op.theta != null ? P[op.theta] : op.angle != null ? op.angle : 0;
    o.state = () => {
      const st = zero(n);
      ops.forEach((op) => applyOp(st, op, theta(op)));
      return st;
    };
    o.probs = () => probsOf(o.state());
    o.labels = () => [...Array(1 << n).keys()].map((i) => bits(i, n));

    const btns = {};
    if (pal) {
      s.gates.forEach((g) => {
        const b = A.el("button", "lab-gate", pal);
        b.textContent = NAME[g] || g.toUpperCase();
        b.style.setProperty("--gc", A.col(PCOL[g] || "gold"));
        b.title = TWO.has(g)
          ? `${b.textContent}: elige el qubit de control y luego el objetivo`
          : `${b.textContent}: elige y haz clic en un cable`;
        b.setAttribute("aria-pressed", "false");
        b.addEventListener("click", () => pick(sel === g ? null : g));
        btns[g] = b;
      });
      const undo = A.el("button", "lab-tool", pal);
      undo.textContent = "Deshacer";
      undo.addEventListener("click", () => {
        const k = ops.findLastIndex((op) => !op.fixed);
        if (k >= 0) {
          ops.splice(k, 1);
          render(true);
        }
      });
      const clear = A.el("button", "lab-tool", pal);
      clear.textContent = "Vaciar";
      clear.addEventListener("click", () => {
        ops = structuredClone(base);
        ctrl = null;
        render(true);
      });
    }
    // Indicación bajo el circuito y, con una puerta elegida, un botón por qubit (para el teclado).
    function showHint() {
      hint.textContent = "";
      if (!editable) return;
      if (!sel) {
        A.el("span", "", hint).textContent =
          "Elige una puerta. Haz clic en una puerta del circuito para quitarla.";
        return;
      }
      const name = NAME[sel] || sel.toUpperCase();
      A.el("span", "", hint).textContent =
        ctrl == null
          ? TWO.has(sel)
            ? `${name}: haz clic en el cable de control`
            : `${name}: haz clic en un cable`
          : `${name}: control en q${sub(ctrl)}; ahora el cable objetivo`;
      for (let q = 0; q < n; q++) {
        if (q === ctrl) continue;
        const b = A.el("button", "lab-q", hint);
        b.textContent = `q${sub(q)}`;
        b.addEventListener("click", () => place(q));
      }
    }
    function pick(g) {
      sel = g;
      ctrl = null;
      for (const [k, b] of Object.entries(btns)) {
        b.classList.toggle("on", k === g);
        b.setAttribute("aria-pressed", String(k === g));
      }
      showHint();
    }
    function place(q) {
      if (!sel) return;
      if (s.maxops && ops.length >= s.maxops) {
        hint.textContent = `Este taller admite hasta ${s.maxops} puertas.`;
        return;
      }
      if (TWO.has(sel)) {
        if (ctrl == null) {
          ctrl = q;
          return showHint();
        }
        if (q === ctrl) {
          ctrl = null;
          return showHint();
        }
        ops.push({ g: sel, q: [ctrl, q] });
        ctrl = null;
      } else ops.push({ g: sel, q: [q] });
      render(true);
    }
    circBox.addEventListener("click", (e) => {
      if (!editable || !o.circ) return;
      const gg = e.target.closest("g.gate"),
        k = gg ? o.circ.groups.indexOf(gg) : -1;
      if (k >= 0 && k < ops.length) {
        if (ops[k].fixed) return;
        ops.splice(k, 1);
        return render(true);
      }
      const svgEl = circBox.querySelector("svg"),
        r = svgEl.getBoundingClientRect();
      const y = ((e.clientY - r.top) * svgEl.viewBox.baseVal.height) / r.height;
      const q = Math.round((y - 38) / 64);
      if (q < 0 || q >= n) return;
      if (!sel) {
        hint.firstChild.textContent = "Primero elige una puerta de la paleta.";
        return;
      }
      place(q);
    });

    function render(changed) {
      for (const [k, sl] of Object.entries(sliders)) sl.set(P[k]);
      const shown = ops.map((op) =>
        op.theta != null ? { ...op, p: fmtAngle(P[op.theta]) } : op,
      );
      // Una columna vacía al final: deja sitio para la próxima puerta.
      if (editable)
        shown.push({
          g: "box",
          q: [...Array(n).keys()],
          label: "  ",
          hidden: true,
        });
      circBox.textContent = "";
      o.circ = B.circuit(
        circBox,
        {
          qubits: n,
          ops: shown,
          maxw: s.cw || 600,
          scale: s.scale || 1.15,
        },
        { ...A, after: () => {} },
      );
      if (editable)
        o.circ.groups.forEach((gg, k) =>
          gg.classList.toggle("rm", k < ops.length && !ops[k].fixed),
        );
      const st = o.state(),
        pr = probsOf(st),
        data = o.labels().map((lab, i) => [lab, pr[i]]);
      if (!o.hist) {
        o.hist = B.hist(
          histBox,
          { data, prob: true, ymax: 1, h: s.hh || 170, digits: 0, w: s.hw },
          A,
        );
      } else o.hist.act({ do: "data", data, dur: changed ? 0.3 : 0 }, !changed);
      if (ketBox) A.tex(ketBox, ketTex(st), true);
      showHint();
      if (changed) A.changed(o);
    }
    o.draw = () => {
      render(false);
      o.hist.draw();
    };
    o.setParam = (k, v) => {
      P[k] = v;
      render(true);
    };
    o.act = (a, instant) => {
      if (a.do === "ops") {
        ops = structuredClone(a.ops);
        render(!instant);
        return true;
      }
      return false;
    };
    o.check = (goal) => {
      const pr = o.probs(),
        labs = o.labels(),
        tol = goal.tol ?? 0.02;
      if (goal.probs)
        return labs.every(
          (lab, i) => Math.abs(pr[i] - (goal.probs[lab] ?? 0)) <= tol,
        );
      return false;
    };
    o.status = () => {
      const pr = o.probs();
      return o
        .labels()
        .map((lab, i) => `P(${lab}) = ${(pr[i] * 100).toFixed(0)} %`)
        .join(" · ");
    };
    render(false);
    return o;
  };

  // ---------------------------------------------------------------- deslizador suelto
  // s: label, min, max, step, value, fmt, targets [{id, p, expr?}]. expr transforma el valor v
  // antes de pasarlo (por ejemplo 'sin(v/2)**2'). Meta: {value: [mín, máx]}.
  B.slider = (box, s, A) => {
    const o = { spec: s, v: s.value ?? s.min ?? 0 };
    box.classList.add("live");
    const fns = (s.targets || []).map((t) =>
      t.expr
        ? new Function("v", `with (Math) { return (${t.expr}); }`)
        : (v) => v,
    );
    const push = () =>
      (s.targets || []).forEach((t, k) => {
        const obj = A.obj(t.id);
        if (!obj) return;
        const v = fns[k](o.v);
        if (obj.setParam) obj.setParam(t.p, v);
        else if (obj.P) {
          obj.P[t.p] = v;
          obj.draw();
        }
      });
    const sl = makeSlider(box, A, s, (v) => {
      o.v = v;
      push();
      A.changed(o);
    });
    o.draw = () => sl.set(o.v);
    o.check = (goal) =>
      !goal.value || (o.v >= goal.value[0] && o.v <= goal.value[1]);
    o.status = () => "";
    A.after(push);
    return o;
  };

  // ---------------------------------------------------------------- máquina de shots
  // s: p (probabilidad de la última etiqueta) o probs, o source (id de un lab); labels; track
  //    (etiqueta que se estima, por defecto la última); verb ('Lanzar', 'Medir'); steps (botones
  //    que suman muestras) o batch (cada clic es una ejecución nueva de ese tamaño); unit.
  // Metas: {n: 1000} (muestras acumuladas) · {batches: 5} (ejecuciones).
  B.shots = (box, s, A) => {
    const o = { spec: s };
    box.classList.add("live");
    let labels = s.labels || ["0", "1"],
      probs = s.probs || [1 - (s.p ?? 0.5), s.p ?? 0.5];
    const src = () => {
      const lab = s.source && A.obj(s.source);
      if (lab) {
        labels = lab.labels();
        probs = lab.probs();
      }
    };
    src();
    const tr = () =>
      Math.max(0, labels.indexOf(s.track ?? labels[labels.length - 1]));
    let counts, N, path, batches;
    const reset = () => {
      counts = labels.map(() => 0);
      N = 0;
      path = [];
      batches = [];
    };
    reset();
    const draw1 = () => {
      const u = Math.random();
      let acc = 0;
      for (let k = 0; k < probs.length; k++) {
        acc += probs[k];
        if (u < acc) return k;
      }
      return probs.length - 1;
    };
    const verb = s.verb || "Medir",
      unit = s.unit || "shots";
    const bar = A.el("div", "shots-bar", box);
    if (s.batch) {
      const b = A.el("button", "lab-gate wide", bar);
      b.textContent = `${verb} ${s.batch} ${unit}`;
      b.addEventListener("click", () => run(s.batch, true));
    } else
      (s.steps || [1, 10, 100, 1000]).forEach((k) => {
        const b = A.el("button", "lab-gate wide", bar);
        b.textContent = `${verb} ${k}`;
        b.addEventListener("click", () => run(k, false));
      });
    const rs = A.el("button", "lab-tool", bar);
    rs.textContent = "Reiniciar";
    rs.addEventListener("click", () => {
      reset();
      paint();
    });
    const grid = A.el("div", "lab-grid", box);
    const histBox = A.el("div", "fig hist", grid);
    const right = A.el("div", "shots-right", grid);
    const chart = A.el("div", "fig shots-chart", right);
    const stats = A.el("div", "shots-stats", right);

    function run(k, fresh) {
      src();
      if (fresh) {
        counts = labels.map(() => 0);
        N = 0;
      }
      const t = tr();
      let next = Math.max(1, N);
      for (let j = 0; j < k; j++) {
        counts[draw1()]++;
        N++;
        // La trayectoria guarda puntos espaciados en escala logarítmica.
        if (!fresh && (N >= next || j === k - 1)) {
          path.push([N, counts[t] / N]);
          next = Math.ceil(N * 1.06);
        }
      }
      if (fresh) batches.push(counts[t] / N);
      paint();
      A.changed(o);
    }
    const W = 470,
      H = 210;
    function paint() {
      const data = labels.map((lab, k) => [lab, counts[k]]);
      const ymax = Math.max(
        10,
        ...counts.map((c) => c * 1.15),
        s.batch ? s.batch * 0.6 : 0,
      );
      histBox.textContent = "";
      o.hist = B.hist(
        histBox,
        { data, h: s.hh || 160, ymax, w: 260, color: "blue" },
        A,
      );
      const t = tr(),
        p = probs[t];
      chart.textContent = "";
      const g = A.svg(
        "svg",
        { width: W, height: H + 40, viewBox: `-46 -10 ${W + 56} ${H + 50}` },
        chart,
      );
      const lo = s.batch ? Math.max(0, p - 0.25) : 0,
        hi = s.batch ? Math.min(1, p + 0.25) : 1;
      const Y = (v) => H - ((v - lo) / (hi - lo)) * H;
      const sig = (n) => sqrt((p * (1 - p)) / n);
      // Eje x: muestras acumuladas (log) o número de ejecución.
      const maxN = s.batch
        ? Math.max(8, batches.length + 1)
        : Math.max(1000, N);
      const X = s.batch
        ? (k) => (k / maxN) * W
        : (n) => (Math.log10(n) / Math.log10(maxN)) * W;
      const band = (m, cls) => {
        const pts = [];
        if (s.batch) {
          const d = m * sig(s.batch);
          pts.push([0, p + d], [W, p + d], [W, p - d], [0, p - d]);
        } else {
          const xs = [];
          for (let e = 0; e <= 1; e += 0.02) xs.push(Math.pow(maxN, e));
          xs.forEach((n) => pts.push([X(n), p + m * sig(n)]));
          xs.toReversed().forEach((n) => pts.push([X(n), p - m * sig(n)]));
        }
        A.svg(
          "polygon",
          {
            points: pts
              .map(([x, v]) => `${x},${Y(Math.min(hi, Math.max(lo, v)))}`)
              .join(" "),
            class: cls,
          },
          g,
        );
      };
      band(2, "band2");
      band(1, "band1");
      A.svg("line", { x1: 0, x2: W, y1: Y(p), y2: Y(p), class: "truth" }, g);
      A.svg("line", { x1: 0, x2: W, y1: H, y2: H, class: "axis" }, g);
      A.svg("line", { x1: 0, x2: 0, y1: 0, y2: H, class: "axis" }, g);
      const txt = (x, y, str, cls, anchor = "middle") => {
        const e = A.svg("text", { x, y, class: cls, "text-anchor": anchor }, g);
        e.textContent = str;
      };
      [lo, p, hi].forEach((v) =>
        txt(-8, Y(v) + 6, v.toFixed(2), "tick", "end"),
      );
      if (s.batch) {
        txt(W / 2, H + 34, "ejecución", "tick");
        batches.forEach((v, k) =>
          A.svg(
            "circle",
            {
              cx: X(k + 1),
              cy: Y(Math.min(hi, Math.max(lo, v))),
              r: 7,
              class: "dot",
            },
            g,
          ),
        );
      } else {
        for (let e = 0; Math.pow(10, e) <= maxN; e++)
          txt(X(Math.pow(10, e)), H + 26, String(Math.pow(10, e)), "tick");
        if (path.length)
          A.svg(
            "polyline",
            {
              points: path.map(([n, v]) => `${X(n)},${Y(v)}`).join(" "),
              class: "path",
            },
            g,
          );
        if (path.length) {
          const [n, v] = path[path.length - 1];
          A.svg("circle", { cx: X(n), cy: Y(v), r: 6, class: "dot" }, g);
        }
      }
      stats.textContent = "";
      const line = (str) => A.rich(A.el("div", "", stats), str);
      const lab = labels[t];
      if (s.batch) {
        line(
          batches.length
            ? `Unos por ejecución: **${batches.map((v) => Math.round(v * s.batch)).join(" · ")}**`
            : `Cada clic es una ejecución nueva de ${s.batch} ${unit}.`,
        );
        line(
          `Esperado: ${Math.round(p * s.batch)} ± ${(sig(s.batch) * s.batch).toFixed(1)} (franja oscura: ±1 error típico)`,
        );
      } else {
        line(
          N
            ? `$N = ${N}$ · \`${lab}\`: ${counts[t]} · $\\hat p = ${(counts[t] / N).toFixed(3)}$`
            : `Pulsa un botón para empezar. La línea marca el valor real $p = ${p.toFixed(2)}$.`,
        );
        if (N)
          line(
            `error típico $\\sqrt{p(1-p)/N} = ${sig(N).toFixed(3)}$ · error real: ${Math.abs(counts[t] / N - p).toFixed(3)}`,
          );
      }
    }
    o.draw = () => paint();
    o.setParam = (k, v) => {
      if (k === "p") probs = [1 - v, v];
      reset();
      paint();
    };
    o.check = (goal) =>
      (!goal.n || N >= goal.n) &&
      (!goal.batches || batches.length >= goal.batches);
    o.status = () =>
      s.batch ? `${batches.length} ejecuciones` : `${N} ${unit}`;
    paint();
    return o;
  };

  // ---------------------------------------------------------------- mapas de kernel
  // s: points [[x, y, clase]] en [0, 1]², ref (punto inicial), gamma, scale, reps, size.
  // Clic en un mapa: nuevo punto de referencia. Cada celda se pinta con k(celda, referencia).
  // Metas: {clicks: 3, scale: [mín, máx], gamma: [mín, máx], reps: [mín, máx]}.
  // El kernel cuántico es el de zz_feature_map(2, reps) de Qiskit sobre (scale·x₀, scale·x₁):
  // por repetición, H en los dos qubits, P(2x₀), P(2x₁) y CX·P(2(π−x₀)(π−x₁))·CX.
  function zzState(x0, x1, reps) {
    const st = zero(2);
    for (let r = 0; r < reps; r++) {
      apply1(st, 0, M1.h());
      apply1(st, 1, M1.h());
      apply1(st, 0, phase(2 * x0));
      apply1(st, 1, phase(2 * x1));
      applyOp(st, { g: "cx", q: [0, 1] });
      apply1(st, 1, phase(2 * (PI - x0) * (PI - x1)));
      applyOp(st, { g: "cx", q: [0, 1] });
    }
    return st;
  }
  const overlap2 = (a, b) => {
    let r = 0,
      m = 0;
    for (let i = 0; i < a.re.length; i++) {
      r += a.re[i] * b.re[i] + a.im[i] * b.im[i];
      m += a.re[i] * b.im[i] - a.im[i] * b.re[i];
    }
    return r * r + m * m;
  };
  B.kernelmap = (box, s, A) => {
    const o = {
      spec: s,
      P: { gamma: s.gamma ?? 5, scale: s.scale ?? 1, reps: s.reps ?? 1 },
      ref: (s.ref || [0.3, 0.6]).slice(),
      clicks: 0,
    };
    box.classList.add("live");
    const S = s.size || 270,
      G = 54;
    const maps = A.el("div", "kmaps", box);
    const mk = (title) => {
      const c = A.el("div", "kmap", maps);
      const t = A.el("div", "ktitle", c);
      const cv = A.el("canvas", "", c);
      cv.width = cv.height = S * 2;
      cv.style.width = cv.style.height = S + "px";
      cv.setAttribute("role", "img");
      return { t, cv, title };
    };
    const rbf = mk("RBF"),
      qk = mk("cuántico");
    const read = A.el("div", "kread", box);
    const kr = (a, b) =>
      Math.exp(-o.P.gamma * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2));
    const kq = (a, b) => {
      const f = (p) =>
        zzState(o.P.scale * p[0], o.P.scale * p[1], Math.round(o.P.reps));
      return overlap2(f(a), f(b));
    };
    function paintMap(m, fn) {
      const ctx = m.cv.getContext("2d"),
        W = m.cv.width,
        c = W / G;
      ctx.clearRect(0, 0, W, W);
      ctx.fillStyle = A.cssv("blue");
      for (let i = 0; i < G; i++)
        for (let j = 0; j < G; j++) {
          ctx.globalAlpha = 0.9 * fn((i + 0.5) / G, 1 - (j + 0.5) / G);
          ctx.fillRect(i * c, j * c, c + 0.5, c + 0.5);
        }
      ctx.globalAlpha = 1;
      (s.points || []).forEach(([x, y, k]) => {
        ctx.beginPath();
        ctx.arc(x * W, (1 - y) * W, 9, 0, 2 * PI);
        ctx.fillStyle = A.cssv(k ? "teal" : "gold");
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = A.cssv("stage");
        ctx.stroke();
      });
      const [rx, ry] = o.ref;
      ctx.beginPath();
      ctx.arc(rx * W, (1 - ry) * W, 16, 0, 2 * PI);
      ctx.lineWidth = 6;
      ctx.strokeStyle = A.cssv("red");
      ctx.stroke();
    }
    function paint() {
      const g = o.P.gamma.toFixed(1),
        sc = o.P.scale.toFixed(2),
        r = Math.round(o.P.reps);
      rbf.t.textContent = `RBF · γ = ${g}`;
      qk.t.textContent = `Cuántico ZZ · escala ${sc} · reps ${r}`;
      paintMap(rbf, (x, y) => kr([x, y], o.ref));
      const refSt = zzState(o.P.scale * o.ref[0], o.P.scale * o.ref[1], r);
      paintMap(qk, (x, y) =>
        overlap2(zzState(o.P.scale * x, o.P.scale * y, r), refSt),
      );
      rbf.cv.setAttribute(
        "aria-label",
        `Similitud RBF con el punto (${o.ref.map((v) => v.toFixed(2)).join(", ")})`,
      );
      qk.cv.setAttribute(
        "aria-label",
        `Similitud del kernel cuántico con el punto (${o.ref.map((v) => v.toFixed(2)).join(", ")})`,
      );
    }
    const at = (cv, e) => {
      const r = cv.getBoundingClientRect();
      return [
        Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)),
        Math.min(1, Math.max(0, 1 - (e.clientY - r.top) / r.height)),
      ];
    };
    const fmt = (v) => v.toFixed(2);
    const idle = () =>
      (read.textContent =
        "Haz clic en un mapa para mover el punto rojo. Pasa el cursor para leer k.");
    [rbf.cv, qk.cv].forEach((cv) => {
      cv.addEventListener("click", (e) => {
        o.ref = at(cv, e);
        o.clicks++;
        paint();
        A.changed(o);
      });
      cv.addEventListener("pointermove", (e) => {
        const p = at(cv, e);
        A.rich(
          read,
          `en (${fmt(p[0])}, ${fmt(p[1])}): $k_{\\rm RBF} = ${kr(p, o.ref).toFixed(2)}$ · $k_{\\rm cuántico} = ${kq(p, o.ref).toFixed(2)}$`,
        );
      });
      cv.addEventListener("pointerleave", idle);
    });
    idle();
    const ctl = A.el("div", "lab-sliders", box);
    const sl = {
      gamma: makeSlider(
        ctl,
        A,
        {
          label: "γ del RBF",
          min: 0.5,
          max: 40,
          step: 0.5,
          value: o.P.gamma,
          digits: 1,
        },
        (v) => o.setParam("gamma", v),
      ),
      scale: makeSlider(
        ctl,
        A,
        {
          label: "escala de los datos",
          min: 0.25,
          max: 6,
          step: 0.25,
          value: o.P.scale,
        },
        (v) => o.setParam("scale", v),
      ),
      reps: makeSlider(
        ctl,
        A,
        { label: "reps", min: 1, max: 3, step: 1, value: o.P.reps, digits: 0 },
        (v) => o.setParam("reps", v),
      ),
    };
    o.setParam = (k, v) => {
      o.P[k] = v;
      sl[k]?.set(v);
      paint();
      A.changed(o);
    };
    o.draw = paint;
    const inside = (v, r) => !r || (v >= r[0] && v <= r[1]);
    o.check = (goal) =>
      o.clicks >= (goal.clicks || 0) &&
      inside(o.P.scale, goal.scale) &&
      inside(o.P.gamma, goal.gamma) &&
      inside(o.P.reps, goal.reps);
    o.status = () =>
      `${o.clicks} ${o.clicks === 1 ? "clic" : "clics"} · escala ${fmt(o.P.scale)} · reps ${Math.round(o.P.reps)}`;
    paint();
    return o;
  };
})();
