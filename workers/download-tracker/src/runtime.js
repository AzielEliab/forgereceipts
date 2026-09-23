/**
 * ForgeReceipts hosted runtime (Cloudflare Worker).
 * Local-style receipt JSON. Not legal advice. No court filing. Does not call Odyssey.
 * /v1/mesh/* is handled by mesh.js (PROXY to aziel-runtime via AZIEL_RUNTIME).
 */
import { meshOpenApiPaths, meshPointer } from "./mesh.js";
import { normalizeAttemptLink } from "./receipt-attempt.js";
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
    clients: [
      "ChatGPT (GPT Actions / OpenAI)",
      "Grok (xAI)",
      "Venice",
      "Claude (Anthropic)",
      "Cursor (MCP)",
      "Glama (MCP)",
      "Perplexity",
      "Microsoft Copilot / Bing",
      "Google Gemini / Vertex",
      "Mistral",
      "Meta AI",
      "Apple Intelligence surfaces",
      "Amazon Q tooling",
      "DuckAssist",
      "You.com",
      "Cohere",
      "other MCP/OpenAPI-capable assistants",
    ],
    author: "Aziel Eliab",
    openapi_import: [
      "Import " + openapi + " as an OpenAPI spec, GPT Action, or custom HTTP tool",
      "Authentication: None",
      "Allow GET /v1/health and the listed POST /v1 routes",
      "Test GET /v1/health, then a sample POST from the spec",
    ],
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
    mcp: [
      "Cursor, Claude, Glama, and other MCP clients: POST https://aziel-runtime.vibelock.workers.dev/mcp",
    ],
    mcp_catalog: "https://aziel-runtime.vibelock.workers.dev/mcp",
    notes: [
      "Any MCP- or OpenAPI-capable assistant can call this runtime. The list above is not exclusive.",
      "GET /download still serves the gzip tarball and increments the counter.",
      "/v1, /openapi.json, and /ai do not increment DOWNLOADS.",
    ],
  };
}

const PRODUCT = "forgereceipts";
const SKILL_MARKDOWN = "---\nname: ForgeReceipts\ndescription: Use when calling ForgeReceipts hosted /v1 or installing the local package. This Worker /v1/mesh/* PROXY to aziel-runtime via AZIEL_RUNTIME. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 cross-map (qnm-node qnsd, no public proxy). No Node Gate. No auto-heal. Not anonymity. Author Aziel Eliab.\n---\n\n# ForgeReceipts\n\nLocal-first evidence integrity packaging. Not legal advice. Does not contact courts, Odyssey, email, or any cloud service. No telemetry. Author: Aziel Eliab.\n\n**THIS IS:** a local-first evidence integrity platform that packages receipts. Hosted /v1 never stores files.\n\n**THIS IS NOT:** legal advice, a court filing, counsel, Odyssey/email/cloud contact, or a guarantee of any court outcome.\n\nAuthor: **Aziel Eliab**. Forks are welcome and always allowed. Apache-2.0.\n\nAlways send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.\n\n## Call these URLs\n\n- Worker OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json\n- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json\n- MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`\n- Live skill (this markdown): `GET https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill`\n\nOps (do **not** increment downloads or views):\n\n| Method | Path | What |\n|--------|------|------|\n| GET | `/v1/health` | Liveness. Does not increment downloads. |\n| GET | `/v1/skill` | This markdown. Does not increment downloads. |\n| GET | `/v1/mesh` | PROXY suite mesh status. Default OFF. QNM live\\|locked\\|isolated. QNS-CD-1.0 cross-map. Never enables. |\n| GET | `/v1/mesh/status` | PROXY alias of GET /v1/mesh. MESH-OK + enabled:false by default. |\n| GET | `/v1/mesh/nodes` | PROXY Live Nodes roster (5-minute presence). |\n| POST | `/v1/mesh/{enable,disable,join,heartbeat,leave,broadcast}` | PROXY. Bearer required to enable. No auto-heal. Anon-broadcast is not a publish path. |\n| GET | `/v1/doctor` | Axes inside the receipt hash: request_id, attempt_n, parent_receipt_id, correlation_id. |\n| POST | `/v1/receipt` | Preview a local receipt hash. request_id, attempt_n, parent_receipt_id, correlation_id, and outcome are inside the hash. Hosted never stores files. |\n\nPOST `/v1/receipt` puts these fields in the hashed canonical body. Changing any of them changes the receipt hash:\n\n- `request_id` — logical original request, same value across retries\n- `attempt_n` — 1-based integer\n- `parent_receipt_id` — prior attempt's receipt hash, null on the first attempt\n- `correlation_id` — optional, sealed as null when omitted\n- `outcome` — `retry`, `failed`, or `completed`\n\nGET `/v1/doctor` lists axes `request_id`, `attempt_n`, `parent_receipt_id`, and `correlation_id`. Receipts without integer `attempt_n` still verify under the older five-field hash. Not a forensic finding. A shared `request_id` is caller-supplied, or minted when omitted. This Worker does not guess that two calls were retries.\n\nWorks with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants. Import the OpenAPI spec, add HTTP tools, or connect via MCP. Public identity: Aziel Eliab only. This Worker `/v1/mesh/*` PROXY to aziel-runtime via AZIEL_RUNTIME. Catalog MCP `mesh_*` + FragGate `slug=mesh`. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer is a hub cite / Worker mesh cross-map only (local `qnsd` in [qnm-node](https://github.com/AzielEliab/qnm-node), runtime cites in [aziel-runtime](https://github.com/AzielEliab/aziel-runtime), pair custody [AZInterface](https://github.com/AzielEliab/azinterface)). Not a Softwares-tab product. No public qnsd proxy. No Node Gate. No auto-heal. Not anonymity. Not legal advice.\n\n## Example\n\n```bash\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/health\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/mesh\ncurl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/mesh/status\ncurl -s -A 'Mozilla/5.0' -X POST https://forgereceipts-download-tracker.vibelock.workers.dev/v1/receipt \\\n  -H 'content-type: application/json' \\\n  -d '{\"sha256\":\"0\"}'\n```\n\n## Local (after one-click install)\n\n```bash\ncurl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash\nforgereceipts ui\n```\n\nThen open http://127.0.0.1:8787 (loopback only).\n\nDOI: https://doi.org/10.5281/zenodo.21436074  \nRecord: https://zenodo.org/records/21436074  \n\nCounted download (gzip HTTP 200, no 302): https://forgereceipts-download-tracker.vibelock.workers.dev/download?asset=forgereceipts-0.3.0.tar.gz\nGitHub: https://github.com/AzielEliab/forgereceipts\n";

const VERSION = "0.3.0";
const BASE = "https://forgereceipts-download-tracker.vibelock.workers.dev";
const BANNER = "Not legal advice. No court filing.";
const MOTTO = "Child's Best Interests First. Integrity Over Narrative. Local Control. Always.";
const GENESIS_PREV_HASH = "0".repeat(64);
const MAX_NOTE = 16384;
export const AXES = Object.freeze([
  "kind",
  "child_impact",
  "evidence",
  "confidence",
  "hash",
  "request_id",
  "attempt_n",
  "parent_receipt_id",
  "correlation_id",
]);

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

/**
 * Legacy seals (no integer attempt_n) hash timestamp, summary, evidence,
 * confidence, prev_hash only. New receipts also hash request_id, attempt_n,
 * parent_receipt_id, correlation_id, and outcome. Changing any of those
 * changes the hash. correlation_id is JSON null when the caller omitted it,
 * so a later value cannot be written onto the same seal.
 * parent_receipt_id is the prior attempt's receipt hash, or null on the first.
 */
export function canonicalBytes(timestamp, summary, evidence, confidence, prevHash, attempt = null) {
  const obj = {
    evidence,
    prev_hash: prevHash,
    summary,
    timestamp,
  };
  if (attempt && attempt.linked) {
    obj.attempt_n = attempt.attempt_n;
    obj.correlation_id = attempt.correlation_id == null ? null : attempt.correlation_id;
    obj.outcome = attempt.outcome == null ? null : attempt.outcome;
    obj.parent_receipt_id = attempt.parent_receipt_id == null ? null : attempt.parent_receipt_id;
    obj.request_id = attempt.request_id == null ? null : attempt.request_id;
  }
  const ordered = Object.keys(obj).concat(["confidence"]).sort();
  const raw =
    "{" +
    ordered
      .map((k) => {
        if (k === "confidence") return JSON.stringify(k) + ":" + formatConfidence(confidence);
        return JSON.stringify(k) + ":" + JSON.stringify(obj[k]);
      })
      .join(",") +
    "}";
  return new TextEncoder().encode(raw);
}

export function storedAttempt(rec) {
  if (!rec || typeof rec !== "object" || !Number.isInteger(rec.attempt_n)) return null;
  return {
    linked: true,
    request_id: rec.request_id == null || rec.request_id === "" ? null : String(rec.request_id),
    attempt_n: rec.attempt_n,
    parent_receipt_id: rec.parent_receipt_id == null || rec.parent_receipt_id === "" ? null : String(rec.parent_receipt_id),
    correlation_id: rec.correlation_id == null || rec.correlation_id === "" ? null : String(rec.correlation_id),
    outcome: typeof rec.outcome === "string" && rec.outcome ? rec.outcome : null,
  };
}

const ATTEMPT_OPENAPI_PROPS = {
  request_id: {
    type: "string",
    description: "Logical original request. Same value across retries. Inside the receipt hash. Omitted mints a new id.",
  },
  attempt_n: {
    type: "integer",
    minimum: 1,
    description: "1-based attempt number. Inside the receipt hash.",
  },
  parent_receipt_id: {
    type: "string",
    nullable: true,
    description: "Prior attempt receipt hash. Null on the first attempt. Inside the receipt hash.",
  },
  correlation_id: {
    type: "string",
    nullable: true,
    description: "Optional client correlation id. Sealed as null when omitted, so setting it later changes the hash.",
  },
  outcome: {
    type: "string",
    enum: ["retry", "failed", "completed"],
    description: "Sealed attempt status inside the receipt hash. completed is the attempt that finished the action.",
  },
};

export function doctorBody() {
  return withBanner({
    ok: true,
    product: PRODUCT,
    version: VERSION,
    op: "doctor",
    doctor: true,
    axes: AXES.slice(),
    author: "Aziel Eliab",
    forensic_claim: false,
    hash_covers_attempt: true,
    note: "ForgeReceipts doctor: request_id, attempt_n, parent_receipt_id, and correlation_id are axes inside the hash. outcome is retry, failed, or completed. parent_receipt_id is the prior attempt receipt hash, or null on the first attempt. correlation_id is sealed null when omitted. Hosted never stores files. Not a forensic finding. Not legal advice. No court filing.",
  });
}

export function openapiDoc() {
  return {
    openapi: "3.1.0",
    info: {
      title: "ForgeReceipts Runtime API",
      version: VERSION,
      summary: MOTTO,
      description: BANNER + " Does not contact Odyssey or any court. Suite mesh /v1/mesh/* PROXY to aziel-runtime (AZIEL_RUNTIME). Default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 cross-map. No Node Gate. No public qnsd proxy. No auto-heal. Not anonymity. Aziel Eliab only.",
    },
    servers: [{ url: BASE }],
    paths: {
      "/v1/health": { get: { operationId: "forgereceiptsHealth", summary: "Liveness", responses: { "200": { description: "OK" } } } },
      "/v1/doctor": {
        get: {
          operationId: "forgereceiptsDoctor",
          summary: "Doctor axes inside the receipt hash: request_id, attempt_n, parent_receipt_id, correlation_id.",
          responses: {
            "200": {
              description: "Doctor JSON. axes lists request_id, attempt_n, parent_receipt_id, correlation_id.",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      axes: {
                        type: "array",
                        items: { type: "string" },
                        description: "kind, child_impact, evidence, confidence, hash, request_id, attempt_n, parent_receipt_id, correlation_id",
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      ...meshOpenApiPaths(),
      "/v1/receipt": {
        post: {
          operationId: "forgereceiptsReceipt",
          summary: "Mint a local-style receipt JSON. Hash covers request_id, attempt_n, parent_receipt_id, correlation_id, and outcome. Not a court filing.",
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
                    ...ATTEMPT_OPENAPI_PROPS,
                  },
                },
              },
            },
          },
          responses: { "200": { description: "Receipt JSON. request_id, attempt_n, parent_receipt_id, correlation_id, and outcome are inside the hash." } },
        },
      },
    },
  };
}

export async function buildReceipt(body, timestamp = utcNow()) {
  const note = body && body.note != null ? String(body.note) : "";
  if (!note.trim()) return { status: 400, payload: withBanner({ ok: false, error: "note is required" }) };
  if (note.length > MAX_NOTE) return { status: 413, payload: withBanner({ ok: false, error: "note too large", max: MAX_NOTE }) };
  const ctx = (body.context && typeof body.context === "object") ? body.context : {};
  const kind = String(ctx.kind || "incident");
  const childImpact = String(ctx.child_impact || ctx.childImpact || "Child's best interests recorded as context for this local receipt.");
  const evidenceBody = String(ctx.evidence || note);
  const summary = String(ctx.summary || note).slice(0, 500);
  const confidence = ctx.confidence == null ? 1.0 : Number(ctx.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    return { status: 400, payload: withBanner({ ok: false, error: "confidence must be a float in [0.0, 1.0]" }) };
  }
  const link = normalizeAttemptLink(body, { generate: true, defaultOutcome: "completed" });
  if (!link.ok) return { status: link.status || 400, payload: withBanner({ ok: false, error: link.error }) };
  const prev = GENESIS_PREV_HASH;
  const evidence = composeEvidence(evidenceBody, kind, childImpact);
  const bytes = canonicalBytes(timestamp, summary, evidence, confidence, prev, link);
  const digest = await sha256Hex(bytes);
  return {
    status: 200,
    payload: withBanner({
      ok: true,
      product: PRODUCT,
      forensic_claim: false,
      receipt: {
        timestamp,
        summary,
        evidence,
        confidence,
        prev_hash: prev,
        hash: digest,
        receipt_id: digest,
        kind,
        child_impact: childImpact,
        note,
        context: ctx,
        request_id: link.request_id,
        attempt_n: link.attempt_n,
        parent_receipt_id: link.parent_receipt_id,
        correlation_id: link.correlation_id,
        outcome: link.outcome,
        hash_covers_attempt: true,
      },
      genesis: true,
      durable: false,
      note_to_caller: "Local-style receipt JSON. request_id, attempt_n, parent_receipt_id, correlation_id, and outcome are inside the hash. parent_receipt_id is the prior attempt hash, or null on the first. Corrections are new receipts. Not a forensic finding. Not legal advice. No court filing. Does not call Odyssey.",
    }),
  };
}

async function handleReceipt(body) {
  const built = await buildReceipt(body);
  return runtimeJson(built.payload, built.status);
}

function receiptFields(src) {
  const rec = src && src.receipt && typeof src.receipt === "object" ? src.receipt : src;
  return rec && typeof rec === "object" ? rec : {};
}

export async function verifyReceipt(body) {
  const rec = receiptFields(body);
  const timestamp = rec.timestamp;
  const summary = rec.summary;
  const evidence = rec.evidence;
  const prev = rec.prev_hash || GENESIS_PREV_HASH;
  const stored = rec.hash ? String(rec.hash) : "";
  if (!timestamp || !summary || !evidence || !stored) {
    return withBanner({
      ok: false,
      product: PRODUCT,
      match: false,
      error: "verify needs receipt.timestamp, summary, evidence, hash",
    });
  }
  const confidence = rec.confidence == null ? 1.0 : Number(rec.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    return withBanner({ ok: false, product: PRODUCT, match: false, error: "confidence must be a float in [0.0, 1.0]" });
  }
  const attempt = storedAttempt(rec);
  const bytes = canonicalBytes(timestamp, summary, evidence, confidence, prev, attempt);
  const recomputed = await sha256Hex(bytes);
  const match = recomputed === stored;
  return withBanner({
    ok: match,
    product: PRODUCT,
    version: VERSION,
    match,
    hash: stored,
    recomputed,
    prev_hash: prev,
    durable: false,
    forensic_claim: false,
    author: "Aziel Eliab",
  });
}

export async function handleRuntime(request, url, env) {
  const path = url.pathname;
  if (path === "/v1/mesh" || path.startsWith("/v1/mesh/")) return null;
  if (path === "/v1/health" && request.method === "GET") {
    return runtimeJson(withBanner({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      axes: AXES.slice(),
      mesh: meshPointer(),
      note: "Hosted /v1 does not store files. Suite mesh /v1/mesh/* PROXY to aziel-runtime. Default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 cross-map. No Node Gate. No public qnsd proxy. No auto-heal. Not anonymity.",
    }));
  }

  if (path === "/v1/doctor" && request.method === "GET") return runtimeJson(doctorBody());
  if (path === "/v1/doctor") return runtimeJson(withBanner({ error: "method not allowed" }), 405);

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
      product: PRODUCT, title: "Use with AI assistants",
      openapi: BASE + "/openapi.json", health: BASE + "/v1/health", mesh: meshPointer(), ...aiHowTo(BASE),
    }));
  }
  if (path === "/v1" && request.method === "GET") {
    return runtimeJson(withBanner({
      product: PRODUCT,
      endpoints: ["GET /v1/health", "GET /v1/doctor", "POST /v1/receipt", "GET /v1/mesh", "GET /v1/mesh/status", "GET /openapi.json", "GET /ai"],
      mesh: meshPointer(),
    }));
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
