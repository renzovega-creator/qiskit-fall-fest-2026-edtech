import { Container, getRandom } from "@cloudflare/containers";

const INSTANCES = 3;

// Una instancia atiende un trabajo a la vez (runner/server.py). El Worker reparte
// entre INSTANCES y reintenta una vez cuando la elegida responde 503.
export class Runner extends Container {
  defaultPort = 8080;
  sleepAfter = "5m";
  enableInternet = false;
}

export default {
  async fetch(request: Request, _env: unknown, ctx: ExecutionContext): Promise<Response> {
    const { pathname } = new URL(request.url);
    if (pathname !== "/run" && pathname !== "/health") {
      return Response.json({ error: "no existe" }, { status: 404 });
    }
    const runners = (ctx as unknown as { exports: { Runner: DurableObjectNamespace<Runner> } })
      .exports.Runner;
    const body = request.method === "POST" ? await request.arrayBuffer() : undefined;
    const send = async () =>
      (await getRandom(runners, INSTANCES)).fetch(
        new Request(request.url, { method: request.method, headers: request.headers, body }),
      );
    const first = await send();
    return first.status === 503 ? send() : first;
  },
};
