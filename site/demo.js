export const DEMO_MODE = globalThis.QG_RUNNER_AVAILABLE === false;

let datos;
async function resultados() {
  datos ??= fetch(new URL("./demo-resultados.json", import.meta.url)).then(
    async (response) => {
      if (!response.ok)
        throw new Error(
          "No se pudieron cargar los resultados de demostración. Recarga la página.",
        );
      return response.json();
    },
  );
  return datos;
}

export function parametrosDemo(id, params) {
  if (!DEMO_MODE) return { ...params };
  const fijos = {
    m1: { shots: 200, seed: 1 },
    m2: { reps: 30, seed: 100 },
    t1: { reps: 20 },
  };
  return { ...params, ...fijos[id] };
}

export function claveMision(id, p) {
  const valores = {
    m1: [p.theta, p.shots, p.seed],
    m2: [p.shots, p.reps, p.seed],
    m3: [p.escala, p.reps],
    t1: [p.shots, p.reps],
  }[id];
  return `${id}:${valores.join(":")}`;
}

export async function resultadoMision(id, params) {
  const out = (await resultados()).misiones[claveMision(id, params)];
  if (!out)
    throw new Error(
      "Esta configuración no está en la demo. Elige un valor de los controles de la misión.",
    );
  return structuredClone(out);
}

export async function resultadoDiario(id) {
  const out = (await resultados()).diario[id];
  if (out === undefined)
    throw new Error("Este reto no está en los resultados de demostración.");
  return out;
}
