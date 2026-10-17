import { createHash, randomUUID } from "node:crypto";

// Sustituye a Google y GitHub como servicio de salida del Worker.
// Conserva los requisitos relevantes: códigos de un solo uso, PKCE,
// credenciales del cliente y `User-Agent` en GitHub.

export type ProviderName = "google" | "github";

export const CLIENTS: Record<ProviderName, { id: string; secret: string }> = {
  google: { id: "google-client", secret: "google-secret" },
  github: { id: "github-client", secret: "github-secret" },
};

const HOSTS: Record<string, ProviderName> = {
  "accounts.google.com": "google",
  "oauth2.googleapis.com": "google",
  "openidconnect.googleapis.com": "google",
  "github.com": "github",
  "api.github.com": "github",
};

interface Grant {
  provider: ProviderName;
  subject: string;
  challenge: string;
  redirectUri: string;
  used: boolean;
}

export interface ProviderCall {
  url: string;
  headers: Record<string, string>;
  form: Record<string, string>;
}

// Lo que un proveedor real también devuelve y el Worker no debe guardar.
// Cada valor es largo y propio de la prueba: un texto corto como «ada» aparece por
// azar en los tokens y hashes base64url y haría la búsqueda intermitente.
export const PII = {
  email: "pii-4417@ejemplo.test",
  name: "Nombre Propio PII-4417",
  login: "login-propio-pii-4417",
};

const sha256url = (text: string) =>
  createHash("sha256").update(text).digest("base64url");

export class FakeProvider {
  readonly calls: ProviderCall[] = [];
  down = new Set<ProviderName>();
  private grants = new Map<string, Grant>();
  private tokens = new Map<string, Grant>();

  owns(url: URL): boolean {
    return url.hostname in HOSTS;
  }

  // El alumno aprueba en la pantalla del proveedor. Devuelve el código que el
  // navegador llevaría de vuelta a la dirección de retorno.
  consent(authorizeUrl: string, subject: string): string {
    const url = new URL(authorizeUrl);
    const provider = HOSTS[url.hostname];
    const q = url.searchParams;
    if (
      !provider ||
      q.get("client_id") !== CLIENTS[provider].id ||
      q.get("response_type") !== "code" ||
      q.get("code_challenge_method") !== "S256" ||
      !q.get("code_challenge") ||
      !q.get("state")
    ) {
      throw new Error(`petición de autorización inválida: ${authorizeUrl}`);
    }
    const code = randomUUID();
    this.grants.set(code, {
      provider,
      subject,
      challenge: q.get("code_challenge")!,
      redirectUri: q.get("redirect_uri")!,
      used: false,
    });
    return code;
  }

  tokenCalls(): ProviderCall[] {
    return this.calls.filter((call) =>
      /\/token$|access_token$/.test(new URL(call.url).pathname),
    );
  }

  async handle(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const provider = HOSTS[url.hostname];
    const headers = Object.fromEntries(request.headers);
    const form =
      request.method === "POST"
        ? Object.fromEntries(new URLSearchParams(await request.text()))
        : {};
    this.calls.push({ url: request.url, headers, form });
    if (this.down.has(provider)) return new Response("caído", { status: 503 });

    if (request.method === "POST") return this.token(provider, headers, form);

    if (provider === "github" && headers["user-agent"] !== "qiskit-guides") {
      return Response.json(
        { message: "Request forbidden by administrative rules" },
        { status: 403 },
      );
    }
    const grant = this.tokens.get(
      headers.authorization?.replace(/^Bearer /, "") ?? "",
    );
    if (!grant || grant.provider !== provider)
      return new Response("no autorizado", { status: 401 });
    return Response.json(
      provider === "google"
        ? { sub: grant.subject, ...PII }
        : { id: Number(grant.subject), ...PII },
    );
  }

  private token(
    provider: ProviderName,
    headers: Record<string, string>,
    form: Record<string, string>,
  ) {
    // GitHub contesta 200 con `error`; Google, 400.
    const reject = (error: string) =>
      provider === "github"
        ? Response.json({ error })
        : Response.json({ error }, { status: 400 });
    const grant = this.grants.get(form.code ?? "");
    const client = CLIENTS[provider];
    if (!grant || grant.provider !== provider) return reject("invalid_grant");
    if (grant.used) return reject("invalid_grant");
    grant.used = true;
    if (form.client_id !== client.id || form.client_secret !== client.secret) {
      return reject("invalid_client");
    }
    if (
      form.grant_type !== "authorization_code" ||
      form.redirect_uri !== grant.redirectUri
    ) {
      return reject("redirect_uri_mismatch");
    }
    if (sha256url(form.code_verifier ?? "") !== grant.challenge)
      return reject("invalid_grant");
    if (provider === "github" && headers.accept !== "application/json") {
      return new Response("access_token=ignored", { status: 200 });
    }
    const token = randomUUID();
    this.tokens.set(token, grant);
    return Response.json({ access_token: token, token_type: "bearer" });
  }
}
