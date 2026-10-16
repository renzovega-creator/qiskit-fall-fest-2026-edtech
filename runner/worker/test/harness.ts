import path from "node:path";

import { build } from "esbuild";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";

// Secretos de prueba documentados por Cloudflare para Turnstile.
export const PASS_SECRET = "1x0000000000000000000000000000000AA";
export const FAIL_SECRET = "2x0000000000000000000000000000000AA";
export const SPENT_SECRET = "3x0000000000000000000000000000000AA";

export const VARS = {
  TURNSTILE_SECRET: PASS_SECRET,
  RATE_PER_MINUTE: "1000",
  RATE_PER_DAY: "100000",
  MAX_CODE_BYTES: "20000",
  MONTHLY_BUDGET_USD: "1000",
  USD_PER_BUSY_SECOND: "0.0000075",
  RESERVED_BUSY_SECONDS: "30",
  SESSION_HOURS: "8",
};

export const TOKEN = "XXXX.DUMMY.TOKEN.XXXX";

let bundle: Promise<string> | undefined;

function bundled(): Promise<string> {
  bundle ??= build({
    entryPoints: [path.join(import.meta.dirname, "entry.ts")],
    bundle: true,
    format: "esm",
    platform: "neutral",
    mainFields: ["module", "main"],
    conditions: ["workerd", "worker"],
    external: ["cloudflare:*"],
    write: false,
    logLevel: "silent",
  }).then((result) => result.outputFiles[0].text);
  return bundle;
}

export interface Reply {
  status: number;
  headers: Headers;
  body: any;
}

export interface Siteverify {
  // Pares clave-valor enviados al servicio de verificación.
  calls: Record<string, string>[];
}

export interface Harness {
  post(
    body: unknown,
    options?: { ip?: string; headers?: Record<string, string>; raw?: string },
  ): Promise<Reply>;
  get(pathname: string): Promise<Reply>;
  // Líneas escritas por el Worker en Workers Logs.
  workerLogs(): string[];
  runnerCalls(): { path: string; headers: string[] }[];
  // Cuántas veces el Worker detuvo una instancia.
  runnerStops(): number;
  siteverify: Siteverify;
  dispose(): Promise<void>;
}

// Simula siteverify: 1x pasa, 2x falla, 3x indica un token usado y `down` no
// responde.
function fakeSiteverify(siteverify: Siteverify, down: boolean) {
  return async (request: Request): Promise<Response> => {
    const form = new URLSearchParams(await request.text());
    siteverify.calls.push(Object.fromEntries(form));
    if (down) return new Response("caído", { status: 502 });
    const secret = form.get("secret") ?? "";
    if (secret.startsWith("1x")) return Response.json({ success: true, "error-codes": [] });
    const code = secret.startsWith("3x") ? "timeout-or-duplicate" : "invalid-input-response";
    return Response.json({ success: false, "error-codes": [code] });
  };
}

export interface Options {
  // FAKE_SETTLE_FAILS hace fallar el ajuste del presupuesto y FAKE_PICKS elige las
  // instancias del contenedor (test/entry.ts).
  vars?: Partial<typeof VARS> & { FAKE_SETTLE_FAILS?: string; FAKE_PICKS?: string };
  // Sin esto el Worker llama al servicio real de Turnstile.
  siteverify?: "fake" | "down" | "real";
}

export async function start(options: Options = {}): Promise<Harness> {
  const logs: string[] = [];
  const siteverify: Siteverify = { calls: [] };
  const mode = options.siteverify ?? "fake";
  const mf = new Miniflare(
    convertV4MiniflareOptions({
      modules: true,
      script: await bundled(),
      scriptPath: path.join(process.cwd(), "worker.mjs"),
      compatibilityDate: "2026-10-01",
      bindings: { ...VARS, ...options.vars },
      durableObjects: {
        Runner: { className: "Runner", useSQLite: true },
        RateLimiter: { className: "RateLimiter", useSQLite: true },
        Budget: { className: "Budget", useSQLite: true },
      },
      ...(mode === "real" ? {} : { outboundService: fakeSiteverify(siteverify, mode === "down") }),
      handleStructuredLogs: (log: { message: string }) => logs.push(log.message),
      logRequests: false,
    }),
  );
  const reply = async (
    response: Awaited<ReturnType<Miniflare["dispatchFetch"]>>,
  ): Promise<Reply> => {
    const text = await response.text();
    let body: any = text;
    try {
      body = JSON.parse(text);
    } catch {}
    return { status: response.status, headers: response.headers as unknown as Headers, body };
  };
  return {
    siteverify,
    post: async (body, { ip = "198.51.100.7", headers = {}, raw } = {}) =>
      reply(
        await mf.dispatchFetch("http://runner.test/run", {
          method: "POST",
          headers: { "content-type": "application/json", "cf-connecting-ip": ip, ...headers },
          body: raw ?? JSON.stringify(body),
        }),
      ),
    get: async (pathname) => reply(await mf.dispatchFetch(`http://runner.test${pathname}`)),
    workerLogs: () => logs.filter((line) => !line.startsWith("FAKE_RUNNER_")),
    runnerStops: () => logs.filter((line) => line === "FAKE_RUNNER_STOP").length,
    runnerCalls: () =>
      logs
        .filter((line) => line.startsWith("FAKE_RUNNER_CALL"))
        .map((line) => JSON.parse(line.slice("FAKE_RUNNER_CALL ".length))),
    dispose: () => mf.dispose(),
  };
}

// Un límite por minuto cuenta ventanas de reloj. Si faltan menos de `ms` para que
// termine la ventana, espera a la siguiente para que la prueba no la cruce.
export async function clearOfMinuteEnd(ms = 8000): Promise<void> {
  const left = 60_000 - (Date.now() % 60_000);
  if (left < ms) await new Promise((resolve) => setTimeout(resolve, left + 50));
}
