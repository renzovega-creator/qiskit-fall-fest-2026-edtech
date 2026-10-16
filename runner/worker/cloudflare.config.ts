import { bindings, defineConfig, defineContainer, exports } from "cf/config";

import * as entrypoint from "./src/index.ts" with { type: "cf-worker" };

const runner = defineContainer({
  name: "qg-runner",
  image: { dockerfile: "../Dockerfile", buildContext: "../.." },
  instanceType: "basic",
  maxInstances: 3,
});

export default defineConfig({
  worker: {
    name: "qg-runner",
    compatibilityDate: "2026-10-01",
    entrypoint,
    // Workers Logs guarda solo lo que escribe src/log.ts. El registro de
    // invocaciones lleva la petición, así que está apagado.
    observability: { enabled: true, logs: { enabled: true, invocationLogs: false } },
    env: {
      // El secreto del widget de Turnstile no se escribe aquí: se crea en la cuenta.
      TURNSTILE_SECRET: bindings.secret(),
      RATE_PER_MINUTE: bindings.text("30"),
      RATE_PER_DAY: bindings.text("1000"),
      MAX_CODE_BYTES: bindings.text("20000"),
      MONTHLY_BUDGET_USD: bindings.text("20"),
      USD_PER_BUSY_SECOND: bindings.text("0.0000075"),
      // 10 s de trabajo, el arranque de la instancia y un reintento tras un 503.
      RESERVED_BUSY_SECONDS: bindings.text("30"),
      SESSION_HOURS: bindings.text("8"),
    },
    exports: {
      Runner: exports.durableObject({ storage: "sqlite", container: runner }),
      RateLimiter: exports.durableObject({ storage: "sqlite" }),
      Budget: exports.durableObject({ storage: "sqlite" }),
    },
  },
  containers: [runner],
});
