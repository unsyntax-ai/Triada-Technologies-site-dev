// Supabase Edge Function: admin-pin
// The admin's 6-digit PIN lock. The PIN is checked HERE, on the server, never in the web page.
// Actions (POST JSON):
//   { action: "unlock", pin }  -> checks the PIN. On success returns a fresh admin sign-in session.
//                                 Each wrong PIN is counted; after 9 wrong tries the lock needs the email code.
//   { action: "set", pin }     -> saves a new PIN. Needs a signed-in admin (the email code sign-in comes first).
// The PIN is stored only as a salted PBKDF2 hash in the admin_pin table, which has no public access.
// Deploy with --no-verify-jwt (see the setup notes): "unlock" is called before anyone is signed in.

const ADMIN_EMAIL = "unsyntax.ai@gmail.com";
const MAX_WRONG = 9;
const ITERATIONS = 210000;
const g = globalThis as any;
const env = (k: string, fallback = "") => g.Deno?.env.get(k) ?? fallback;
const SUPABASE_URL = env("SUPABASE_URL", "https://evofqeolhdlteyztrzin.supabase.co");
const ANON_KEY = env("SUPABASE_ANON_KEY");
const SERVICE_KEY = env("SUPABASE_SERVICE_ROLE_KEY");

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-region",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function reply(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });
}

const enc = new TextEncoder();
const toHex = (b: Uint8Array) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
const fromHex = (h: string) => Uint8Array.from(h.match(/../g) ?? [], (x) => parseInt(x, 16));

async function hashPin(pin: string, salt: Uint8Array): Promise<string> {
  const key = await crypto.subtle.importKey("raw", enc.encode(pin), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations: ITERATIONS }, key, 256);
  return toHex(new Uint8Array(bits));
}

// compares every character, so timing does not reveal how close a wrong PIN was
function same(a: string, b: string) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

const OBVIOUS = ["123456", "234567", "345678", "456789", "567890", "654321", "987654"];
const validPin = (p: unknown): p is string => typeof p === "string" && /^\d{6}$/.test(p);

// ---------- the PIN row (service role only) ----------
const rest = (path: string, init: RequestInit = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`, "Content-Type": "application/json", Prefer: "return=representation", ...(init.headers as any) },
  });

async function readRow() {
  const r = await rest("admin_pin?id=eq.1&select=salt,hash,failed");
  if (!r.ok) throw new Error("PIN store unavailable");
  const rows = await r.json();
  return rows[0] ?? null;
}

async function writeRow(fields: Record<string, unknown>) {
  const r = await rest("admin_pin?id=eq.1", { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ ...fields, updated_at: new Date().toISOString() }) });
  if (!r.ok) throw new Error("PIN store unavailable");
}

// lets the counter update finish after the reply has gone out; returns false when the runtime cannot do that
function later(p: Promise<unknown>): boolean {
  p.catch(() => {});
  const rt = (g as any).EdgeRuntime;
  if (rt && typeof rt.waitUntil === "function") { rt.waitUntil(p); return true; }
  return false;
}

// ---------- session for the admin, issued only after a correct PIN ----------
async function adminSession() {
  const link = await fetch(`${SUPABASE_URL}/auth/v1/admin/generate_link`, {
    method: "POST",
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ type: "magiclink", email: ADMIN_EMAIL }),
  });
  if (!link.ok) throw new Error("Could not start the admin session");
  const { hashed_token } = await link.json();
  const r = await fetch(`${SUPABASE_URL}/auth/v1/verify`, {
    method: "POST",
    headers: { apikey: ANON_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ type: "magiclink", token_hash: hashed_token }),
  });
  const s = await r.json();
  if (!r.ok || !s.access_token) throw new Error("Could not start the admin session");
  return { access_token: s.access_token, refresh_token: s.refresh_token, expires_in: s.expires_in };
}

// ---------- actions ----------
async function unlock(pin: unknown) {
  if (!validPin(pin)) return reply({ state: "wrong", attempts_left: MAX_WRONG });
  // step timings (milliseconds) are returned so a slow sign-in can be traced; they reveal nothing about the PIN
  const ms: Record<string, number> = {};
  const t0 = performance.now();
  const lap = (k: string, from: number) => { ms[k] = Math.round(performance.now() - from); };
  // the sign-in session is prepared at once, alongside the database read and the PIN check, so a correct PIN does not
  // wait for it; it is only handed out when the PIN is right
  const ts = performance.now();
  const sessionReady = adminSession().then((s) => { lap("session", ts); return s; });
  sessionReady.catch(() => {});
  const t = performance.now();
  const row = await readRow();
  lap("read", t);
  if (!row) return reply({ state: "no_pin" });
  if (row.failed >= MAX_WRONG) return reply({ state: "locked" });
  const h = performance.now();
  const ok = same(await hashPin(pin, fromHex(row.salt)), row.hash);
  lap("hash", h);
  if (!ok) {
    const failed = row.failed + 1;
    const w = performance.now();
    const saved = writeRow({ failed });
    if (!later(saved)) await saved;
    lap("write", w);
    lap("total", t0);
    if (failed >= MAX_WRONG) return reply({ state: "locked" });
    return reply({ state: "wrong", attempts_left: MAX_WRONG - failed, ms });
  }
  if (row.failed > 0) { const reset = writeRow({ failed: 0 }); if (!later(reset)) await reset; }
  const session = await sessionReady;
  lap("total", t0);
  return reply({ state: "ok", session, ms });
}

async function setPin(req: Request, pin: unknown) {
  // only a signed-in admin may set the PIN
  const auth = req.headers.get("authorization") ?? "";
  const who = await fetch(`${SUPABASE_URL}/auth/v1/user`, { headers: { Authorization: auth, apikey: ANON_KEY } });
  if (!who.ok) return reply({ error: "Please sign in again." }, 401);
  const user = await who.json();
  if ((user.email ?? "").toLowerCase() !== ADMIN_EMAIL) return reply({ error: "Not allowed." }, 403);
  if (!validPin(pin)) return reply({ error: "The PIN must be 6 digits." }, 400);
  if (/^(\d)\1{5}$/.test(pin) || OBVIOUS.includes(pin)) {
    return reply({ error: "Choose a less obvious PIN." }, 400);
  }

  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await hashPin(pin, salt);
  const exists = await readRow();
  if (exists) await writeRow({ salt: toHex(salt), hash, failed: 0 });
  else {
    const r = await rest("admin_pin", { method: "POST", body: JSON.stringify({ id: 1, salt: toHex(salt), hash, failed: 0 }) });
    if (!r.ok) throw new Error("PIN store unavailable");
  }
  return reply({ ok: true });
}

if (g.Deno) {
  g.Deno.serve(async (req: Request) => {
    if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
    if (req.method !== "POST") return reply({ error: "Use POST." }, 405);
    try {
      const body = await req.json().catch(() => ({}));
      if (body.action === "ping") {   // warm-up from the admin page: wakes the function and opens its connections
        await Promise.allSettled([readRow(), fetch(`${SUPABASE_URL}/auth/v1/health`, { headers: { apikey: ANON_KEY } })]);
        return reply({ ok: true });
      }
      if (body.action === "unlock") return await unlock(body.pin);
      if (body.action === "set") return await setPin(req, body.pin);
      return reply({ error: "Unknown action." }, 400);
    } catch (e) {
      return reply({ error: "Something went wrong. Try again." }, 500);
    }
  });
}
