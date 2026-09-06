/**
 * Offline + live check for /v1/mesh/* PROXY.
 * GET /v1/mesh/status must be MESH-OK style JSON with enabled:false by default.
 */
import { handleMesh, meshOkFallback, parseMeshDoc, publicMesh } from "../src/mesh.js";

function fail(msg) {
  console.error("verify-mesh-proxy: " + msg);
  process.exit(1);
}

const fallback = meshOkFallback({ op: "status", source: "fallback" });
if (fallback.code !== "MESH-OK") fail("fallback code");
if (fallback.enabled !== false) fail("fallback must be enabled:false");
if (fallback.author !== "Aziel Eliab" || fallback.identity !== "Aziel Eliab") fail("identity");

const parsed = parseMeshDoc(fallback);
if (parsed.enabled) fail("parseMeshDoc must stay off");
const pub = publicMesh(parsed);
if (pub.enabled_default === false && pub.enabled === false && pub.product === "forgereceipts") {
  /* ok */
} else {
  fail("publicMesh contract");
}

const mockReq = new Request("https://forgereceipts-download-tracker.vibelock.workers.dev/v1/mesh/status", {
  method: "GET",
  headers: { "user-agent": "Mozilla/5.0" },
});
const mockUrl = new URL(mockReq.url);
const mockEnv = {
  AZIEL_RUNTIME: {
    async fetch() {
      return new Response(JSON.stringify(meshOkFallback({ op: "status", source: "binding" })), {
        headers: { "content-type": "application/json" },
      });
    },
  },
};
const proxied = await handleMesh(mockReq, mockUrl, mockEnv);
if (!proxied) fail("handleMesh returned null");
const body = await proxied.json();
if (body.code !== "MESH-OK") fail("proxied code " + body.code);
if (body.enabled !== false) fail("proxied enabled");

const skipped = await handleMesh(new Request("https://example.test/v1/health"), new URL("https://example.test/v1/health"), {});
if (skipped != null) fail("non-mesh path must return null");

console.log("verify-mesh-proxy: MESH-OK enabled:false (binding mock) ok");
