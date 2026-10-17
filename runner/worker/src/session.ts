const COOKIE = "qg_session";
const TURNSTILE_URL =
  "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const MAX_TOKEN_CHARS = 2048;

const encoder = new TextEncoder();

function hex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// HMAC-SHA256 con una clave derivada del secreto de Turnstile y de una etiqueta,
// para que la cookie y el nombre del limitador no compartan clave.
export async function mac(
  secret: string,
  label: string,
  message: string,
): Promise<string> {
  const root = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const derived = await crypto.subtle.sign("HMAC", root, encoder.encode(label));
  const key = await crypto.subtle.importKey(
    "raw",
    derived,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return hex(await crypto.subtle.sign("HMAC", key, encoder.encode(message)));
}

// La cookie lleva solo la hora de caducidad y un MAC que cubre esa hora y la IP.
// No identifica a nadie y no sirve desde otra IP.
export async function issueSession(
  secret: string,
  ip: string,
  now: number,
  ttlMs: number,
): Promise<string> {
  const expires = Math.floor(now + ttlMs);
  const tag = await mac(secret, "session", `${expires}|${ip}`);
  const maxAge = Math.ceil(ttlMs / 1000);
  return `${COOKIE}=${expires}.${tag}; Max-Age=${maxAge}; Path=/run; HttpOnly; Secure; SameSite=Strict`;
}

export function getCookie(
  cookieHeader: string | null,
  name: string,
): string | undefined {
  return cookieHeader
    ?.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export async function hasSession(
  secret: string,
  ip: string,
  now: number,
  cookieHeader: string | null,
): Promise<boolean> {
  const value = getCookie(cookieHeader, COOKIE);
  const [expires, tag] = value?.split(".") ?? [];
  if (!expires || !tag || !/^\d+$/.test(expires) || Number(expires) <= now)
    return false;
  const expected = await mac(secret, "session", `${expires}|${ip}`);
  return (
    expected.length === tag.length &&
    crypto.subtle.timingSafeEqual(encoder.encode(expected), encoder.encode(tag))
  );
}

export type Verification = "ok" | "rejected" | "unavailable";

// Solo se envían el secreto y el token; la IP del alumno no sale del Worker.
export async function verifyTurnstile(
  secret: string,
  token: string,
): Promise<Verification> {
  if (token.length > MAX_TOKEN_CHARS) return "rejected";
  try {
    const response = await fetch(TURNSTILE_URL, {
      method: "POST",
      body: new URLSearchParams({ secret, response: token }),
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) return "unavailable";
    const result = (await response.json()) as { success?: boolean };
    return result.success === true ? "ok" : "rejected";
  } catch {
    return "unavailable";
  }
}
