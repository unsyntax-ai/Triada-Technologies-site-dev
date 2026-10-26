// Supabase Edge Function: contact
// Receives the website's contact form, keeps a copy in the contact_messages table, and emails it to the team's
// Outlook mailbox through Microsoft Graph (the Microsoft 365 mail service), so nothing goes through a third party.
//
// POST JSON: { name, company, email, phone, reason, message, website, t }
//   website  hidden "trap" field: real visitors leave it empty, bots fill it in
//   t        milliseconds the visitor spent on the form: bots submit instantly
//
// Secrets this function needs (Supabase > Edge Functions > Secrets):
//   MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET   the Microsoft app that may send mail (see supabase/README-contact.md)
//   MAIL_FROM   the mailbox the message is sent as and from (hr@triadatechnologies.com)
//   MAIL_TO     where the messages arrive (hr@triadatechnologies.com)
//   IP_SALT     any long random text; visitors' addresses are stored only as a salted hash, for the rate limit
//   ALLOWED_ORIGINS  optional, comma separated; defaults to the live site, www and the dev site
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase itself.
// Deploy with --no-verify-jwt: visitors are not signed in.

const g = globalThis as any;
const DEFAULT_ORIGINS = "https://triadatechnologies.com,https://www.triadatechnologies.com,https://unsyntax-ai.github.io";
const REASONS: Record<string, string> = { client: "Hiring talent", candidate: "Looking for work", vendor: "A vendor or partner" };
const PER_IP_PER_HOUR = 5;
const PER_DAY_TOTAL = 300;

export type Deps = { env: (k: string) => string; fetch: typeof fetch; now: () => number };

const realDeps: Deps = {
  env: (k) => g.Deno?.env.get(k) ?? g.process?.env?.[k] ?? "",
  fetch: (...a) => fetch(...a),
  now: () => Date.now(),
};

// ---------- small helpers ----------
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] as string));
const oneLine = (s: string) => s.replace(/[\r\n\t]+/g, " ").trim();
const clean = (v: unknown, max: number) => (typeof v === "string" ? v.trim().slice(0, max) : "");

async function sha256(text: string) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(b), (x) => x.toString(16).padStart(2, "0")).join("");
}

function validate(b: any) {
  const f = {
    name: clean(b.name, 80), company: clean(b.company, 100), email: clean(b.email, 120),
    phone: clean(b.phone, 30), reason: clean(b.reason, 20), message: clean(b.message, 2000),
  };
  const bad: Record<string, string> = {};
  if (f.name.length < 2 || !/[A-Za-zÀ-ɏ]/.test(f.name)) bad.name = "Enter your full name.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.email)) bad.email = "Enter a valid email address.";
  if (f.phone) {
    const d = f.phone.replace(/\D/g, "");
    if (!/^\+?[\d\s().-]+$/.test(f.phone) || d.length < 10 || d.length > 15) bad.phone = "Enter the full phone number with area code, or leave it empty.";
  }
  if (f.message.length < 10) bad.message = "Add a little more detail (at least 10 characters).";
  if (!(f.reason in REASONS)) f.reason = "client";
  return { f, bad };
}

function cors(origin: string | null, allowed: string[]) {
  const h: Record<string, string> = {
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-region",
    "Access-Control-Allow-Methods": "POST, OPTIONS", "Vary": "Origin",
  };
  if (origin && allowed.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

// ---------- the database (service role only) ----------
function rest(d: Deps, path: string, init: RequestInit = {}) {
  const key = d.env("SUPABASE_SERVICE_ROLE_KEY");
  return d.fetch(`${d.env("SUPABASE_URL")}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", ...(init.headers as any) },
  });
}

async function countSince(d: Deps, filter: string, sinceMs: number) {
  const since = new Date(d.now() - sinceMs).toISOString();
  const r = await rest(d, `contact_messages?select=id&created_at=gte.${encodeURIComponent(since)}${filter}`, {
    headers: { Prefer: "count=exact", Range: "0-0" },
  });
  const total = (r.headers.get("content-range") ?? "").split("/")[1];
  return total && total !== "*" ? parseInt(total, 10) : 0;
}

// ---------- the email, through Microsoft Graph ----------
let cached: { token: string; until: number } | null = null;

async function graphToken(d: Deps) {
  if (cached && cached.until > d.now() + 60_000) return cached.token;
  const r = await d.fetch(`https://login.microsoftonline.com/${d.env("MS_TENANT_ID")}/oauth2/v2.0/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: d.env("MS_CLIENT_ID"), client_secret: d.env("MS_CLIENT_SECRET"),
      scope: "https://graph.microsoft.com/.default", grant_type: "client_credentials",
    }).toString(),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.access_token) throw new Error("Microsoft sign-in failed: " + (j.error_description ?? j.error ?? r.status).toString().slice(0, 200));
  cached = { token: j.access_token, until: d.now() + (j.expires_in ?? 3600) * 1000 };
  return j.access_token as string;
}

async function sendMail(d: Deps, f: ReturnType<typeof validate>["f"], id: string) {
  const token = await graphToken(d);
  const who = REASONS[f.reason];
  const rows: [string, string][] = [["Name", f.name], ["Company", f.company || "-"], ["Email", f.email], ["Phone", f.phone || "-"], ["I am", who]];
  const html = `<div style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;color:#111">
<p style="margin:0 0 12px"><b>New message from the website contact form</b></p>
<table style="border-collapse:collapse">${rows.map(([k, v]) => `<tr><td style="padding:3px 14px 3px 0;color:#555">${k}</td><td>${esc(v)}</td></tr>`).join("")}</table>
<p style="margin:16px 0 4px;color:#555">Message</p>
<div style="white-space:pre-wrap;border-left:3px solid #FF6A00;padding-left:12px">${esc(f.message)}</div>
<p style="margin:18px 0 0;color:#888;font-size:12px">Press Reply to answer ${esc(f.name)} directly. Saved as ${esc(id)}.</p></div>`;
  const r = await d.fetch(`https://graph.microsoft.com/v1.0/users/${encodeURIComponent(d.env("MAIL_FROM"))}/sendMail`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      message: {
        subject: oneLine(`Website message from ${f.name} (${who})`),
        body: { contentType: "HTML", content: html },
        toRecipients: [{ emailAddress: { address: d.env("MAIL_TO") } }],
        replyTo: [{ emailAddress: { address: f.email, name: oneLine(f.name) } }],
      },
      saveToSentItems: false,
    }),
  });
  if (!r.ok) throw new Error("Microsoft Graph sendMail " + r.status + ": " + (await r.text()).slice(0, 200));
}

// ---------- the handler ----------
export async function handle(req: Request, d: Deps = realDeps): Promise<Response> {
  const allowed = (d.env("ALLOWED_ORIGINS") || DEFAULT_ORIGINS).split(",").map((s) => s.trim());
  const headers = { ...cors(req.headers.get("origin"), allowed), "Content-Type": "application/json" };
  const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers });

  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return reply({ error: "Use POST." }, 405);
  const origin = req.headers.get("origin");
  if (origin && !allowed.includes(origin)) return reply({ error: "Not allowed." }, 403);

  let b: any;
  try { b = await req.json(); } catch { return reply({ error: "Send the form as JSON." }, 400); }
  if (!b || typeof b !== "object") return reply({ error: "Send the form as JSON." }, 400);

  // bots: the hidden field is filled in, or the form was sent faster than a person could fill it. Pretend all is well.
  if (clean(b.website, 200) || (typeof b.t === "number" && b.t < 1000)) return reply({ ok: true });

  const { f, bad } = validate(b);
  if (Object.keys(bad).length) return reply({ error: "Please check the form.", fields: bad }, 400);

  try {
    const ip = (req.headers.get("cf-connecting-ip") ?? req.headers.get("x-forwarded-for") ?? "unknown").split(",")[0].trim();
    const ipHash = await sha256(ip + "|" + (d.env("IP_SALT") || "triada"));
    if ((await countSince(d, `&ip_hash=eq.${ipHash}`, 3_600_000)) >= PER_IP_PER_HOUR) return reply({ error: "Too many messages. Please try again later, or call or email us." }, 429);
    if ((await countSince(d, "", 86_400_000)) >= PER_DAY_TOTAL) return reply({ error: "We are very busy right now. Please email us directly." }, 503);

    const saved = await rest(d, "contact_messages", {
      method: "POST", headers: { Prefer: "return=representation" },
      body: JSON.stringify({ ...f, ip_hash: ipHash, user_agent: clean(req.headers.get("user-agent"), 200) }),
    });
    if (!saved.ok) throw new Error("could not save: " + saved.status);
    const id: string = (await saved.json())[0]?.id ?? "";

    try {
      await sendMail(d, f, id);
      await rest(d, `contact_messages?id=eq.${id}`, { method: "PATCH", body: JSON.stringify({ emailed: true }) });
    } catch (e) {
      // the message is safely saved; note why the email failed so it can be found and fixed
      console.error("email failed:", String((e as Error).message));
      await rest(d, `contact_messages?id=eq.${id}`, { method: "PATCH", body: JSON.stringify({ email_error: String((e as Error).message).slice(0, 300) }) }).catch(() => {});
    }
    return reply({ ok: true });
  } catch (e) {
    console.error("contact failed:", String((e as Error).message));
    return reply({ error: "Something went wrong on our side. Please email us directly." }, 500);
  }
}

if (g.Deno) g.Deno.serve((req: Request) => handle(req));
