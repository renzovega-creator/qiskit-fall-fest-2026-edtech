import { DurableObject } from "cloudflare:workers";

import real, { Budget as RealBudget } from "../src/index.ts";

// Sustituye la imagen por un contenedor falso que registra las cabeceras, nunca
// el cuerpo, y responde con el contrato de /run.
export { RateLimiter } from "../src/index.ts";

// Un Budget real cuyo almacenamiento falla al ajustar el coste cuando la prueba
// lo pide con la variable FAKE_SETTLE_FAILS.
export class Budget extends RealBudget {
  override async settle(month: string, reserved: number, actual: number): Promise<void> {
    if ((this.env as { FAKE_SETTLE_FAILS?: string }).FAKE_SETTLE_FAILS) {
      throw new Error("StorageDown: el almacenamiento no responde");
    }
    return super.settle(month, reserved, actual);
  }
}

interface TestEnv {
  // Instancias que elige el Worker, en orden, separadas por comas ("0,1").
  FAKE_PICKS?: string;
}

let picked = false;

export default {
  async fetch(request: Request, env: TestEnv, ctx: ExecutionContext): Promise<Response> {
    const runners = (ctx as unknown as { exports: { Runner: DurableObjectNamespace } }).exports
      .Runner;
    // Otro alumno que ya tiene un trabajo en la instancia 0, sin pasar por el Worker.
    if (new URL(request.url).pathname === "/other-learner") {
      return runners
        .get(runners.idFromName("instance-0"))
        .fetch(
          new Request("http://runner/run", {
            method: "POST",
            body: JSON.stringify({ code: "ajeno" }),
          }),
        );
    }
    if (env.FAKE_PICKS && !picked) {
      picked = true;
      const picks = env.FAKE_PICKS.split(",").map(Number);
      // getRandom elige con Math.random: así la prueba decide qué instancia toca.
      Math.random = () => ((picks.shift() ?? 0) + 0.5) / 3;
    }
    return real.fetch(request, env as never, ctx);
  },
};

export class Runner extends DurableObject {
  // Verdadero mientras la instancia atiende el trabajo de otro alumno.
  private busy = false;
  private killed = false;

  async fetch(request: Request): Promise<Response> {
    const headers = [...request.headers.keys()].sort();
    console.log(
      `FAKE_RUNNER_CALL ${JSON.stringify({ path: new URL(request.url).pathname, headers })}`,
    );
    const { code } = (await request.json()) as { code: string };
    if (code === "romper-contenedor") throw new Error("ContainerDown: la instancia se cayó");
    if (code === "ajeno") {
      this.busy = true;
      this.killed = false;
      await scheduler.wait(900);
      this.busy = false;
      if (this.killed) throw new Error("ContainerKilled: la instancia se detuvo");
    } else if (this.busy) {
      // Como runner/server.py: sin ranura libre responde 503 y no espera.
      return Response.json({ error: "ocupado" }, { status: 503 });
    } else {
      // Un trabajo que no termina a tiempo: solo el Worker puede cortarlo.
      await scheduler.wait(code === "colgar" ? 1500 : 15);
    }
    return Response.json({
      passed: true,
      stdout: `recibidos ${code.length} caracteres\n`,
      error: null,
      tests: [],
      ms: 15,
      killed: null,
      peak_mb: 1,
    });
  }

  // Container.destroy() mata la instancia.
  async destroy(): Promise<void> {
    if (this.busy) this.killed = true;
    console.log("FAKE_RUNNER_STOP");
  }
}
