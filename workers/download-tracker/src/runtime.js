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
const EXAMPLE_PAYLOAD = {
  "summary": "filed locally",
  "evidence": "sha256:demo"
};

const SKILL_MARKDOWN = "---\nname: ForgeReceipts\ndescription: Use when calling ForgeReceipts hosted /v1 or installing the local package. Author Aziel Eliab.\n---\n\n# ForgeReceipts\n\nLocal-first evidence integrity packaging. Not legal advice. Does not contact courts, Odyssey, email, or any cloud service. No telemetry. Author: Aziel Eliab.\n\n**THIS IS:** a local-first evidence integrity platform that packages receipts. Hosted /v1 never stores files.\n\n**THIS IS NOT:** legal advice, a court filing, counsel, Odyssey/email/cloud contact, or a guarantee of any court outcome.\n\nAuthor: **Aziel Eliab**. Forks are welcome and always allowed. Apache-2.0.\n\nAlways send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.\n\n## Call these URLs\n\n- Worker OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json\n- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json\n- MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`\n- Live skill (this markdown): `GET https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill`\n\nOps (do **not** increment downloads or views):\n\n| Method | Path | What |\n|--------|------|------|\n| GET | `/v1/health` | Liveness. Does not increment downloads. |\n| GET | `/v1/skill` | This markdown. Does not increment downloads. |\n| POST | `/v1/receipt` | Preview a local receipt hash. Hosted never stores files. |\n\nGrok: import OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.\n\n## Example\n\n```bash\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/health\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill\ncurl -s -A 'Mozilla/5.0' -X POST https://forgereceipts-download-tracker.vibelock.workers.dev/v1/receipt \\\n  -H 'content-type: application/json' \\\n  -d '{\"sha256\":\"0\"}'\n```\n\n## Local (after one-click install)\n\n```bash\ncurl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash\nforgereceipts ui\n```\n\nThen open http://127.0.0.1:8787 (loopback only).\n\nDOI: https://doi.org/10.5281/zenodo.21436074  \nRecord: https://zenodo.org/records/21436074  \n\nCounted download (gzip HTTP 200, no 302): https://forgereceipts-download-tracker.vibelock.workers.dev/download?asset=forgereceipts-0.2.0.tar.gz\nGitHub: https://github.com/AzielEliab/forgereceipts\n\n## Catalog + local UI\n\nAuthor: **Aziel Eliab**. Honest scope: Local receipt / checklist helper. Not legal advice. Does not contact courts.\n\n- Catalog product: https://aziel-runtime.vibelock.workers.dev/p/forgereceipts/\n- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json\n- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`\n- This Worker skill: `GET https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill`\n- This Worker OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json\n- Sample payload: `GET https://forgereceipts-download-tracker.vibelock.workers.dev/v1/example`\n\nLocal UI: **Import JSON file** (`type=file`) and **Export JSON**. Then `forgereceipts doctor`.\n\nGrok: import catalog or Worker OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.\n";

const VERSION = "0.2.0";
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
            "/v1/example": { get: { operationId: "forgereceiptsExample", summary: "Sample JSON payload. Does not increment downloads.", responses: { "200": { description: "OK" } } } },
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
    return runtimeJson(withBanner({ ok: true, author: "Aziel Eliab", product: PRODUCT, version: VERSION }));
  }
  if ((path === "/v1/example" || path === "/v1/example/") && (request.method === "GET" || request.method === "HEAD")) {
    return runtimeJson({
      ok: true,
      product: PRODUCT,
      author: "Aziel Eliab",
      example: EXAMPLE_PAYLOAD,
      note: "Sample payload only. Does not increment downloads.",
    });
  }


  if (path === "/v1/skill" && request.method === "GET") {
    return new Response(SKILL_MARKDOWN, {
      status: 200,
      headers: {
        "Content-Type": "text/markdown; charset=utf-8",
        "Cache-Control": "private, no-store",
        "X-KV-Increment": "false",
        "Access-Control-Allow-Origin": "*",
      },
    });
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
