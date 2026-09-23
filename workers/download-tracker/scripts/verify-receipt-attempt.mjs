/**
 * Retry linkage on the standalone download-tracker receipt.
 * Same note with attempt_n 1 vs 2 must change the hash.
 * Author: Aziel Eliab. Not a court filing. Not a forensic finding.
 */
import assert from "node:assert/strict";
import {
  AXES,
  buildReceipt,
  canonicalBytes,
  doctorBody,
  handleRuntime,
  openapiDoc,
  verifyReceipt,
} from "../src/runtime.js";

const REQ = "req_chain_demo_0001";
const TS = "2026-09-23T00:00:00Z";
const CITE = ["request_id", "attempt_n", "parent_receipt_id", "correlation_id"];

function link(attempt_n, parent_receipt_id, outcome, correlation_id = null) {
  return {
    linked: true,
    request_id: REQ,
    attempt_n,
    parent_receipt_id,
    correlation_id,
    outcome,
  };
}

const evidence = "KIND: incident\nCHILD_IMPACT: sample\n\nsame";
const bytes1 = canonicalBytes(TS, "same", evidence, 1, "0".repeat(64), link(1, null, "retry"));
const bytes2 = canonicalBytes(TS, "same", evidence, 1, "0".repeat(64), link(2, null, "retry"));
const bytesCorr = canonicalBytes(TS, "same", evidence, 1, "0".repeat(64), link(1, null, "retry", "corr_demo"));
const bytesLegacy = canonicalBytes(TS, "same", evidence, 1, "0".repeat(64), null);
const text1 = new TextDecoder().decode(bytes1);
const text2 = new TextDecoder().decode(bytes2);
assert.notEqual(text1, text2);
assert.notEqual(text1, new TextDecoder().decode(bytesCorr));
assert.equal(text1.includes('"attempt_n":1'), true);
assert.equal(text2.includes('"attempt_n":2'), true);
assert.equal(text1.includes('"request_id":"' + REQ + '"'), true);
assert.equal(text1.includes('"correlation_id":null'), true);
assert.equal(new TextDecoder().decode(bytesCorr).includes('"correlation_id":"corr_demo"'), true);
assert.equal(new TextDecoder().decode(bytesLegacy).includes("attempt_n"), false);

async function sha256Hex(bytes) {
  const dig = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(dig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
assert.notEqual(await sha256Hex(bytes1), await sha256Hex(bytes2));

const legacyHash = await sha256Hex(bytesLegacy);
const legacy = await verifyReceipt({
  receipt: {
    timestamp: TS,
    summary: "same",
    evidence,
    confidence: 1,
    prev_hash: "0".repeat(64),
    hash: legacyHash,
    context: { attempt_n: 2, request_id: REQ },
  },
});
assert.equal(legacy.match, true, "older seals stay valid when attempt_n was not in the hash");

const r1 = await buildReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 1,
  parent_receipt_id: null,
  correlation_id: "corr_demo",
  outcome: "retry",
}, TS);
const r2 = await buildReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 2,
  parent_receipt_id: r1.payload.receipt.hash,
  correlation_id: "corr_demo",
  outcome: "retry",
}, TS);
const r3 = await buildReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 3,
  parent_receipt_id: r2.payload.receipt.hash,
  correlation_id: "corr_demo",
  outcome: "completed",
}, TS);
assert.equal(r1.status, 200);
assert.equal(r2.status, 200);
assert.equal(r3.status, 200);
assert.equal(r1.payload.receipt.request_id, REQ);
assert.equal(r2.payload.receipt.request_id, REQ);
assert.equal(r3.payload.receipt.request_id, REQ);
assert.equal(r1.payload.receipt.attempt_n, 1);
assert.equal(r2.payload.receipt.attempt_n, 2);
assert.equal(r3.payload.receipt.attempt_n, 3);
assert.equal(r1.payload.receipt.parent_receipt_id, null);
assert.equal(r2.payload.receipt.parent_receipt_id, r1.payload.receipt.hash);
assert.equal(r3.payload.receipt.parent_receipt_id, r2.payload.receipt.hash);
assert.equal(r1.payload.receipt.receipt_id, r1.payload.receipt.hash);
assert.notEqual(r1.payload.receipt.hash, r2.payload.receipt.hash);
assert.notEqual(r2.payload.receipt.hash, r3.payload.receipt.hash);
assert.equal(r1.payload.receipt.outcome, "retry");
assert.equal(r2.payload.receipt.outcome, "retry");
assert.equal(r3.payload.receipt.outcome, "completed");
assert.equal(r1.payload.forensic_claim, false);
assert.equal((await verifyReceipt({ receipt: r1.payload.receipt })).match, true);
assert.equal((await verifyReceipt({ receipt: r2.payload.receipt })).match, true);
assert.equal((await verifyReceipt({ receipt: r3.payload.receipt })).match, true);
const tampered = { ...r2.payload.receipt, attempt_n: 1 };
assert.equal((await verifyReceipt({ receipt: tampered })).match, false);

const fromContext1 = await buildReceipt({
  note: "same",
  context: { request_id: REQ, attempt_n: 1, parent_receipt_id: null, outcome: "retry" },
}, TS);
const fromContext2 = await buildReceipt({
  note: "same",
  context: {
    request_id: REQ,
    attempt_n: 2,
    parent_receipt_id: fromContext1.payload.receipt.hash,
    outcome: "failed",
  },
}, TS);
assert.equal(fromContext1.payload.receipt.context.attempt_n, 1);
assert.notEqual(fromContext1.payload.receipt.hash, fromContext2.payload.receipt.hash);
assert.equal(fromContext2.payload.receipt.request_id, REQ);
assert.equal(fromContext2.payload.receipt.parent_receipt_id, fromContext1.payload.receipt.hash);

const omitted = await buildReceipt({ note: "same", request_id: REQ, attempt_n: 1, outcome: "retry" }, TS);
const correlated = await buildReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 1,
  outcome: "retry",
  correlation_id: "corr_later",
}, TS);
assert.equal(omitted.payload.receipt.correlation_id, null);
assert.notEqual(omitted.payload.receipt.hash, correlated.payload.receipt.hash);

const bad = await buildReceipt({ note: "same", attempt_n: 0 }, TS);
assert.equal(bad.status, 400);
const badOutcome = await buildReceipt({ note: "same", outcome: "forensic" }, TS);
assert.equal(badOutcome.status, 400);

const spec = openapiDoc();
const props = spec.paths["/v1/receipt"].post.requestBody.content["application/json"].schema.properties;
for (const name of [...CITE, "outcome"]) {
  assert.ok(props[name], "openapi property " + name);
}
assert.deepEqual(props.outcome.enum, ["retry", "failed", "completed"]);
const doctor = doctorBody();
for (const name of CITE) {
  assert.ok(doctor.axes.includes(name), "doctor axis " + name);
  assert.ok(AXES.includes(name), name);
}
assert.equal(doctor.forensic_claim, false);
assert.match(spec.paths["/v1/doctor"].get.summary, /request_id/);

const base = "https://forgereceipts-download-tracker.vibelock.workers.dev";
const doctorRes = await handleRuntime(new Request(base + "/v1/doctor"), new URL(base + "/v1/doctor"), {});
const doctorJson = await doctorRes.json();
assert.equal(doctorRes.status, 200);
for (const name of CITE) assert.ok(doctorJson.axes.includes(name), name);

const openRes = await handleRuntime(new Request(base + "/openapi.json"), new URL(base + "/openapi.json"), {});
const openJson = await openRes.json();
const liveProps = openJson.paths["/v1/receipt"].post.requestBody.content["application/json"].schema.properties;
for (const name of [...CITE, "outcome"]) assert.ok(liveProps[name], name);

async function postReceipt(body) {
  const res = await handleRuntime(
    new Request(base + "/v1/receipt", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
    new URL(base + "/v1/receipt"),
    {},
  );
  return res.json();
}
const http1 = await postReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 1,
  parent_receipt_id: null,
  outcome: "retry",
});
const http2 = await postReceipt({
  note: "same",
  request_id: REQ,
  attempt_n: 2,
  parent_receipt_id: http1.receipt.hash,
  outcome: "completed",
});
assert.equal(http1.receipt.request_id, http2.receipt.request_id);
assert.equal(http1.receipt.attempt_n, 1);
assert.equal(http2.receipt.attempt_n, 2);
assert.equal(http2.receipt.parent_receipt_id, http1.receipt.hash);
assert.notEqual(http1.receipt.hash, http2.receipt.hash);
assert.equal((await verifyReceipt({ receipt: http1.receipt })).match, true);
assert.equal((await verifyReceipt({ receipt: http2.receipt })).match, true);

console.log("ok receipt-attempt: hashed request_id / attempt_n / parent_receipt_id / correlation_id / outcome");
