/**
 * Attempt linkage for new ForgeReceipts receipts.
 *
 * Groups several attempts under one logical request. Each attempt is its own
 * receipt. parent_receipt_id is the prior attempt's receipt hash.
 * This Worker does not store receipts and does not invent parent links.
 *
 * Additive on new receipts. Receipts sealed without integer attempt_n keep
 * the previous five-field canonical body. Not a court filing. Not a forensic finding.
 *
 * Author: Aziel Eliab. Identity is Aziel Eliab only.
 * SPDX-License-Identifier: Apache-2.0
 */

export const ATTEMPT_FIELDS = Object.freeze([
  "request_id",
  "attempt_n",
  "parent_receipt_id",
  "correlation_id",
]);

export const OUTCOMES = Object.freeze(["retry", "failed", "completed"]);

const ID_RE = /^[A-Za-z0-9_.:-]{1,128}$/;

export function newRequestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return "req_" + [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function sourcesOf(input) {
  const sources = [];
  if (!input || typeof input !== "object") return sources;
  sources.push(input);
  if (input.attempt_link && typeof input.attempt_link === "object") sources.push(input.attempt_link);
  if (input.attempt && typeof input.attempt === "object") sources.push(input.attempt);
  if (input.context && typeof input.context === "object") sources.push(input.context);
  if (input.payload && typeof input.payload === "object") sources.push(input.payload);
  return sources;
}

function hasOwn(sources, key) {
  return sources.some(
    (src) => src && typeof src === "object" && Object.prototype.hasOwnProperty.call(src, key) && src[key] !== undefined,
  );
}

function first(sources, key) {
  for (const src of sources) {
    if (!src || typeof src !== "object") continue;
    if (!Object.prototype.hasOwnProperty.call(src, key)) continue;
    if (src[key] === undefined) continue;
    return src[key];
  }
  return undefined;
}

/**
 * Normalize caller attempt fields.
 * generate:true mints request_id when the caller omitted one.
 * Does not look up prior receipts. Callers that have a chain pass parent_receipt_id.
 */
export function normalizeAttemptLink(input, opts = {}) {
  const sources = sourcesOf(input);
  const attemptSupplied = hasOwn(sources, "attempt_n");
  const parentSupplied = hasOwn(sources, "parent_receipt_id");
  const correlationSupplied = hasOwn(sources, "correlation_id");
  const outcomeSupplied = hasOwn(sources, "outcome");
  const requestSupplied = hasOwn(sources, "request_id");

  let request_id = null;
  if (requestSupplied) {
    const raw = first(sources, "request_id");
    request_id = raw == null || raw === "" ? "" : String(raw).trim();
  }
  if (!request_id) {
    if (requestSupplied) {
      return { ok: false, error: "request_id must be 1-128 chars [A-Za-z0-9_.:-]", status: 400 };
    }
    request_id = opts.generate === false ? null : newRequestId();
  }
  if (request_id && !ID_RE.test(request_id)) {
    return { ok: false, error: "request_id must be 1-128 chars [A-Za-z0-9_.:-]", status: 400 };
  }

  let attempt_n = 1;
  if (attemptSupplied) {
    const raw = first(sources, "attempt_n");
    if (raw == null || raw === "") {
      attempt_n = 1;
    } else {
      const n = typeof raw === "number" ? raw : Number(raw);
      if (!Number.isInteger(n) || n < 1 || n > 100000) {
        return { ok: false, error: "attempt_n must be an integer >= 1", status: 400 };
      }
      attempt_n = n;
    }
  }

  let parent_receipt_id = null;
  if (parentSupplied) {
    const raw = first(sources, "parent_receipt_id");
    if (raw != null && raw !== "") {
      parent_receipt_id = String(raw).trim();
      if (!ID_RE.test(parent_receipt_id)) {
        return { ok: false, error: "parent_receipt_id must be a prior receipt hash or id", status: 400 };
      }
    }
  }

  let correlation_id = null;
  if (correlationSupplied) {
    const raw = first(sources, "correlation_id");
    if (raw != null && raw !== "") {
      correlation_id = String(raw).trim();
      if (!ID_RE.test(correlation_id)) {
        return { ok: false, error: "correlation_id must be 1-128 chars [A-Za-z0-9_.:-]", status: 400 };
      }
    }
  }

  let outcome = opts.defaultOutcome || "completed";
  if (outcomeSupplied) {
    const raw = first(sources, "outcome");
    if (raw != null && raw !== "") {
      outcome = String(raw).trim().toLowerCase();
      if (!OUTCOMES.includes(outcome)) {
        return { ok: false, error: "outcome must be retry, failed, or completed", status: 400 };
      }
    }
  }

  return {
    ok: true,
    linked: true,
    request_id,
    attempt_n,
    parent_receipt_id,
    correlation_id,
    outcome,
    request_supplied: requestSupplied,
    attempt_supplied: attemptSupplied,
    parent_supplied: parentSupplied,
    correlation_supplied: correlationSupplied,
    outcome_supplied: outcomeSupplied,
  };
}
