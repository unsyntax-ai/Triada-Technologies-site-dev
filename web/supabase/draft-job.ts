// Supabase Edge Function: draft-job
// Organises a pasted job description into the listing form WITHOUT changing a single word of it.
// How: the text is cut into numbered pieces. The AI only decides which piece belongs where
// (summary, responsibilities, requirements) and picks out the title, location, pay and type.
// This code then builds the listing from the original pieces, so the wording can never be altered.
// Only the admin can call it. The Groq key is read from the secret GROQ_API_KEY.

const ADMIN_EMAIL = "unsyntax.ai@gmail.com";
const g = globalThis as any;
const SUPABASE_URL: string = g.Deno?.env.get("SUPABASE_URL") ?? "https://evofqeolhdlteyztrzin.supabase.co";
// Tried in order. If Groq retires or does not offer one, the next is used.
const MODELS = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"];
const TYPES = ["Contract", "Contract-to-hire", "Direct hire", "Temporary"];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function reply(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });
}

// ---------- cutting the text into pieces (formatting only, words untouched) ----------
const BULLET = /^\s*(?:[-*•●▪–·]|\d{1,2}[.)])\s+/;

export function segment(notes: string): string[] {
  const out: string[] = [];
  for (const raw of notes.replace(/\r/g, "").split("\n")) {
    const line = raw.replace(BULLET, "").trim();
    if (!line) continue;
    if (line.length > 280) {
      // A long paragraph: cut at sentence ends so each piece is one sentence.
      for (const s of line.split(/(?<=[.!?])\s+(?=[A-Z0-9(])/)) if (s.trim()) out.push(s.trim());
    } else out.push(line);
  }
  return out.slice(0, 120);
}

const norm = (t: string) => t.toLowerCase().replace(/[^a-z0-9$%+#.]+/g, " ").trim();
// A value the AI quotes (title, location, pay) is accepted only if it really appears in the text.
const quoted = (value: unknown, notes: string) => {
  const v = String(value ?? "").trim();
  return v && norm(notes).includes(norm(v)) ? v : "";
};
const ids = (v: unknown, n: number): number[] =>
  [...new Set((Array.isArray(v) ? v : []).map((x) => Number(x)).filter((x) => Number.isInteger(x) && x >= 0 && x < n))];

export function build(notes: string, ai: Record<string, unknown>) {
  const parts = segment(notes);
  const n = parts.length;
  const resp = ids(ai.responsibility_ids, n);
  const req = ids(ai.requirement_ids, n).filter((i) => !resp.includes(i));
  // Only short heading-like pieces ("Responsibilities:", "Requirements") may be dropped.
  const heads = ids(ai.heading_ids, n).filter((i) => parts[i].length <= 50 && !resp.includes(i) && !req.includes(i));
  const used = new Set([...resp, ...req, ...heads]);
  const given = new Set(ids(ai.summary_ids, n).filter((i) => !used.has(i)));
  const rest = parts.map((_, i) => i).filter((i) => !used.has(i) && !given.has(i));
  const summaryIds = [...given, ...rest].sort((a, b) => a - b);

  const confirm: string[] = [];
  if (rest.length) confirm.push(`${rest.length} line(s) were not clearly a duty or a requirement, so they were kept under Summary exactly as written.`);

  let title = quoted(ai.title, notes);
  // If the AI did not quote a title, use the first line of the text when it is short enough to be one.
  if (!title && parts[0] && parts[0].length <= 100 && !/[:.]$/.test(parts[0])) title = parts[0];
  if (!title) confirm.push("The job title was not clear in the text. Please type it.");
  let location = quoted(ai.location, notes);
  if (!location) { location = "Remote (U.S.)"; confirm.push("No location was found in the text. 'Remote (U.S.)' is a placeholder. Please check it."); }
  const pay = quoted(ai.pay, notes);
  const type = TYPES.includes(String(ai.employment_type)) ? String(ai.employment_type) : "Contract";
  if (!TYPES.includes(String(ai.employment_type))) confirm.push("The contract type was not clear. Please check it.");

  return {
    title: title.slice(0, 120),
    location: location.slice(0, 120),
    employment_type: type,
    pay: pay.slice(0, 120),
    summary: summaryIds.map((i) => parts[i]).join("\n"),
    responsibilities: resp.sort((a, b) => a - b).map((i) => parts[i]),
    requirements: req.sort((a, b) => a - b).map((i) => parts[i]),
    confirm,
  };
}

// ---------- the AI part: sort the numbered pieces, never rewrite ----------
const SYSTEM = `You are sorting a job description for a staffing firm. You must NOT rewrite, shorten, correct or add any wording.
You are given the text as numbered pieces, starting at 0. Return a JSON object that points to pieces by number.
Keys:
- "title": the job title, copied exactly as it appears in the text (or "").
- "location": the work location, copied exactly as it appears (or "").
- "pay": the pay or rate, copied exactly as it appears (or "" if the text gives none).
- "employment_type": exactly one of: ${TYPES.join(", ")}. Choose the closest match to the text.
- "summary_ids": numbers of pieces that describe the role, the team or the company in general.
- "responsibility_ids": numbers of pieces that describe duties or what the person will do.
- "requirement_ids": numbers of pieces that describe skills, experience, education or qualifications needed.
- "heading_ids": numbers of pieces that are only a section label such as "Responsibilities:" or "Requirements".
Every piece number must appear in at most one list. If you are unsure where a piece belongs, put it in "summary_ids". Never invent text.`;

async function sort(parts: string[], groqKey: string) {
  const numbered = parts.map((p, i) => `${i}: ${p}`).join("\n");
  let last = "";
  for (const model of MODELS) {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${groqKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        temperature: 0,
        response_format: { type: "json_object" },
        messages: [{ role: "system", content: SYSTEM }, { role: "user", content: `Job description pieces:\n${numbered}` }],
      }),
    });
    if (!r.ok) {
      let detail = "";
      try { detail = (await r.json()).error?.message ?? ""; } catch { /* ignore */ }
      last = `${model}: ${r.status} ${detail}`.trim();
      if (r.status === 401) throw new Error("Groq rejected the key. Check the GROQ_API_KEY secret.");
      continue;
    }
    try { return JSON.parse((await r.json()).choices[0].message.content); } catch { last = `${model}: unreadable answer`; }
  }
  throw new Error(`The AI service could not sort this text. ${last}`.slice(0, 300));
}

if (g.Deno) {
  g.Deno.serve(async (req: Request) => {
    if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
    if (req.method !== "POST") return reply({ error: "Use POST." }, 405);

    // 1. Only the signed-in admin may use this.
    const auth = req.headers.get("authorization") ?? "";
    const apikey = req.headers.get("apikey") ?? "";
    const who = await fetch(`${SUPABASE_URL}/auth/v1/user`, { headers: { Authorization: auth, apikey } });
    if (!who.ok) return reply({ error: "Please sign in again." }, 401);
    const user = await who.json();
    if ((user.email ?? "").toLowerCase() !== ADMIN_EMAIL) return reply({ error: "Not allowed." }, 403);

    // 2. Read the pasted text.
    let notes = "";
    try { notes = String((await req.json()).notes ?? "").trim(); } catch { /* fall through */ }
    if (notes.length < 20) return reply({ error: "Paste the job description first." }, 400);
    if (notes.length > 12000) return reply({ error: "The text is too long. Keep it under 12000 characters." }, 400);
    const groqKey = g.Deno.env.get("GROQ_API_KEY");
    if (!groqKey) return reply({ error: "The Groq key is not set in Supabase secrets." }, 500);

    // 3. Sort the pieces, then build the listing from the original words.
    try {
      const ai = await sort(segment(notes), groqKey);
      return reply(build(notes, ai));
    } catch (e) {
      return reply({ error: (e as Error).message }, 502);
    }
  });
}
