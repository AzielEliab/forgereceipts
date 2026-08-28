/**
 * ForgeReceipts hosted runtime (Cloudflare Worker).
 * Local-style receipt JSON. Not legal advice. No court filing. Does not call Odyssey.
 */
function runtimeCors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function runtimeJson(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...runtimeCors() },
  });
}

async function sha256Hex(bytes) {
  const data = bytes instanceof Uint8Array ? bytes : new TextEncoder().encode(String(bytes));
  const dig = await crypto.subtle.digest("SHA-256", data);
  const arr = new Uint8Array(dig);
  let out = "";
  for (let i = 0; i < arr.length; i++) out += arr[i].toString(16).padStart(2, "0");
  return out;
}

async function readJsonBody(request) {
  const ct = (request.headers.get("content-type") || "").toLowerCase();
  if (request.method === "GET" || request.method === "HEAD") return {};
  const text = await request.text();
  if (!text || !text.trim()) return {};
  try {
    return JSON.parse(text);
  } catch {
    const err = new Error("JSON body required");
    err.status = 400;
    throw err;
  }
}

function utcNow() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function aiHowTo(base) {
  const openapi = base + "/openapi.json";
  const health = base + "/v1/health";
  return {
    chatgpt_actions: [
      "Open GPT Editor → Actions → Import from URL",
      "Paste " + openapi,
      "Authentication: None",
      "Allow GET /v1/health and the listed POST /v1 routes",
      "Test GET /v1/health, then a sample POST from the spec",
    ],
    grok_xai_tools: [
      "Add an HTTP / OpenAPI tool pointing at " + openapi,
      "Or register GET /v1/health, GET /openapi.json, and the product POSTs",
      "No API key. CORS is *",
    ],
    venice_http_tools: [
      "Add an HTTP tool with method, URL, and JSON body from " + openapi,
      "Start with GET " + health,
      "Then call the product POST listed in the spec",
    ],
    mcp_catalog: "https://aziel-runtime.vibelock.workers.dev/mcp",
    notes: [
      "GET /download still serves the gzip tarball and increments the counter.",
      "/v1, /openapi.json, and /ai do not increment DOWNLOADS.",
    ],
  };
}

const PRODUCT = "forgereceipts";
const VERSION = "0.1.0";
const BASE = "https://forgereceipts-download-tracker.vibelock.workers.dev";
const BANNER = "Not legal advice. No court filing.";
const MOTTO = "Child's Best Interests First. Integrity Over Narrative. Local Control. Always.";
const GENESIS_PREV_HASH = "0".repeat(64);
const MAX_NOTE = 16384;

function withBanner(obj) {
  return {
    banner: BANNER,
    motto: MOTTO,
    legal_advice: false,
    court_filing: false,
    odyssey: false,
    court: false,
    ...obj,
  };
}

function formatConfidence(c) {
  const n = Number(c);
  const v = Number.isFinite(n) ? n : 1;
  return v.toFixed(6);
}

function composeEvidence(body, kind, childImpact) {
  const lines = [
    "KIND: " + kind,
    "CHILD_IMPACT: " + String(childImpact || "").trim(),
    "",
    (body && String(body).trim()) ? String(body).trim() : "(no additional body)",
  ];
  return lines.join("\n");
}

function canonicalBytes(timestamp, summary, evidence, confidence, prevHash) {
  const obj = {
    confidence: "__TL_CONFIDENCE__",
    evidence,
    prev_hash: prevHash,
    summary,
    timestamp,
  };
  const keys = Object.keys(obj).sort();
  let raw = "{" + keys.map((k) => JSON.stringify(k) + ":" + JSON.stringify(obj[k])).join(",") + "}";
  raw = raw.replace('"__TL_CONFIDENCE__"', formatConfidence(confidence));
  return new TextEncoder().encode(raw);
}

function openapiDoc() {
  return {
    openapi: "3.1.0",
    info: {
      title: "ForgeReceipts Runtime API",
      version: VERSION,
      summary: MOTTO,
      description: BANNER + " Does not contact Odyssey or any court.",
    },
    servers: [{ url: BASE }],
    paths: {
      "/v1/health": { get: { operationId: "forgereceiptsHealth", summary: "Liveness", responses: { "200": { description: "OK" } } } },
      "/v1/receipt": {
        post: {
          operationId: "forgereceiptsReceipt",
          summary: "Mint a local-style receipt JSON (not a court filing)",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  required: ["note"],
                  properties: {
                    note: { type: "string" },
                    context: { type: "object", additionalProperties: true },
                  },
                },
              },
            },
          },
          responses: { "200": { description: "Receipt JSON" } },
        },
      },
    },
  };
}

async function handleReceipt(body) {
  const note = body && body.note != null ? String(body.note) : "";
  if (!note.trim()) return runtimeJson(withBanner({ ok: false, error: "note is required" }), 400);
  if (note.length > MAX_NOTE) return runtimeJson(withBanner({ ok: false, error: "note too large", max: MAX_NOTE }), 413);
  const ctx = (body.context && typeof body.context === "object") ? body.context : {};
  const kind = String(ctx.kind || "incident");
  const childImpact = String(ctx.child_impact || ctx.childImpact || "Child's best interests recorded as context for this local receipt.");
  const evidenceBody = String(ctx.evidence || note);
  const summary = String(ctx.summary || note).slice(0, 500);
  const confidence = ctx.confidence == null ? 1.0 : Number(ctx.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    return runtimeJson(withBanner({ ok: false, error: "confidence must be a float in [0.0, 1.0]" }), 400);
  }
  const timestamp = utcNow();
  const prev = GENESIS_PREV_HASH;
  const evidence = composeEvidence(evidenceBody, kind, childImpact);
  const bytes = canonicalBytes(timestamp, summary, evidence, confidence, prev);
  const digest = await sha256Hex(bytes);
  return runtimeJson(withBanner({
    ok: true,
    product: PRODUCT,
    receipt: {
      timestamp,
      summary,
      evidence,
      confidence,
      prev_hash: prev,
      hash: digest,
      kind,
      child_impact: childImpact,
      note,
      context: ctx,
    },
    genesis: true,
    durable: false,
    note_to_caller: "Local-style receipt JSON. Corrections are new receipts. Not legal advice. No court filing. Does not call Odyssey.",
  }));
}

export async function handleRuntime(request, url, env) {
  const path = url.pathname;
  if (path === "/v1/health" && request.method === "GET") {
    return runtimeJson(withBanner({ ok: true, product: PRODUCT, version: VERSION }));
  }
  if (path === "/openapi.json" && request.method === "GET") return runtimeJson(openapiDoc());
  if (path === "/ai" && request.method === "GET") {
    return runtimeJson(withBanner({
      product: PRODUCT, title: "Use with Grok, ChatGPT, Venice",
      openapi: BASE + "/openapi.json", health: BASE + "/v1/health", ...aiHowTo(BASE),
    }));
  }
  if (path === "/v1" && request.method === "GET") {
    return runtimeJson(withBanner({ product: PRODUCT, endpoints: ["GET /v1/health", "POST /v1/receipt", "GET /openapi.json", "GET /ai"] }));
  }
  if (path === "/v1/receipt" && request.method === "POST") {
    let body = {};
    try { body = await readJsonBody(request); } catch (e) { return runtimeJson(withBanner({ ok: false, error: e.message }), e.status || 400); }
    return handleReceipt(body);
  }
  if (path === "/v1/receipt") return runtimeJson(withBanner({ error: "method not allowed" }), 405);
  if (path.startsWith("/v1/")) return runtimeJson(withBanner({ error: "not found", product: PRODUCT }), 404);
  return null;
}
