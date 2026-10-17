import http from "node:http";

import { start } from "./harness.ts";

// Un Worker local con el proveedor falso para las pruebas de navegador.
// Imprime los orígenes del sitio y del control, y sirve hasta SIGTERM.
// El control solo escucha en 127.0.0.1 y expone el consentimiento falso y
// los recuentos de filas de la base.
const TABLES = ["users", "identities", "sessions", "lesson_done", "exercise_state", "kv"];

const harness = await start();
const site = await harness.origin();

const control = http.createServer(async (req, res) => {
  const send = (status: number, body: unknown) => {
    res.writeHead(status, { "content-type": "application/json" }).end(JSON.stringify(body));
  };
  try {
    if (req.method === "GET" && req.url === "/rows") {
      const rows: Record<string, number> = {};
      for (const table of TABLES) {
        const count = await harness.db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).first<number>("n");
        rows[table] = count ?? 0;
      }
      return send(200, rows);
    }
    if (req.method === "POST" && req.url === "/consent") {
      let text = "";
      for await (const chunk of req) text += chunk;
      const { authorizeUrl, subject } = JSON.parse(text);
      return send(200, { code: harness.provider.consent(authorizeUrl, subject) });
    }
    send(404, { error: "no existe" });
  } catch (error) {
    send(500, { error: String(error) });
  }
});
await new Promise<void>((ready) => control.listen(0, "127.0.0.1", ready));
const { port } = control.address() as { port: number };
console.log(JSON.stringify({ site, control: `http://127.0.0.1:${port}` }));

process.on("SIGTERM", async () => {
  control.close();
  await harness.dispose();
  process.exit(0);
});
