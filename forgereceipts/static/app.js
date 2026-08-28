
(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text, status: res.status }; }
    data._status = res.status;
    return data;
  }

  function show(mode) {
    $$("[data-panel]").forEach((el) => el.classList.toggle("hidden", el.getAttribute("data-panel") !== mode));
    $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
    history.replaceState(null, "", "#" + mode);
  }

  function receiptCard(r) {
    const div = document.createElement("div");
    div.className = "receipt";
    const impact = r.child_impact ? `<div><em>Child impact:</em> ${escapeHtml(r.child_impact)}</div>` : "";
    const priv = r.private_note ? `<div><em>Private note:</em> ${escapeHtml(r.private_note)}</div>` : "";
    const file = r.file_sha256 ? `<div class="hash">file ${escapeHtml(r.file_name || "")} ${escapeHtml(r.file_sha256)}</div>` : "";
    div.innerHTML = `<strong>${escapeHtml(r.summary || "")}</strong>
      <div class="muted">${escapeHtml(r.timestamp || "")} · ${escapeHtml(r.kind || "")} · conf ${r.confidence}</div>
      ${impact}${priv}${file}
      <div class="hash">${escapeHtml(r.hash || "")}</div>`;
    return div;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  async function refreshLock() {
    const st = await api("/api/lock");
    const overlay = $("#lock-overlay");
    if (st.lock_set && !st.unlocked) overlay.classList.remove("hidden");
    else overlay.classList.add("hidden");
    $("#lk-out").textContent = JSON.stringify(st, null, 2);
    return st;
  }

  async function refreshHome() {
    const score = await api("/api/score");
    $("#pss").textContent = (score.score ?? "—") + "";
    $("#pss-bar").style.width = Math.max(0, Math.min(100, score.score || 0)) + "%";
    $("#pss-note").textContent = score.disclaimer || "";
    const legal = await api("/api/legal?jurisdiction=IN");
    const box = $("#legal-box");
    box.innerHTML = `<div class="card"><h2>Legal reference (stub)</h2>
      <p class="help">${escapeHtml(legal.disclaimer || "Not legal advice.")}</p>
      <p class="muted">${escapeHtml((legal.jurisdiction && legal.jurisdiction.stub) || "")}</p>
      ${(legal.baseline || []).map((b) => `<div class="blurb"><strong>${escapeHtml(b.name)}</strong> <span class="muted">${escapeHtml(b.cite)}</span><p>${escapeHtml(b.blurb)}</p></div>`).join("")}
    </div>`;
  }

  async function refreshIncidents() {
    const data = await api("/api/receipts?kind=incident");
    const list = $("#inc-list");
    list.innerHTML = "";
    (data.receipts || []).slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
  }

  async function refreshJournal() {
    const data = await api("/api/receipts?kind=journal");
    const list = $("#j-list");
    list.innerHTML = "";
    (data.receipts || []).slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
  }

  async function refreshFiling() {
    const t = await api("/api/filing");
    $("#f-check").innerHTML = `<p class="help">${escapeHtml(t.disclaimer || "")}</p>
      <ol>${(t.efiling_checklist || []).map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ol>`;
  }

  $$("#nav button").forEach((b) => b.addEventListener("click", () => {
    const mode = b.dataset.mode;
    show(mode);
    if (mode === "home") refreshHome();
    if (mode === "incident") refreshIncidents();
    if (mode === "journal") refreshJournal();
    if (mode === "filing") refreshFiling();
    if (mode === "lock") refreshLock();
  }));

  $("#inc-save").addEventListener("click", async () => {
    $("#inc-err").textContent = "";
    const data = await api("/api/incident", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        summary: $("#inc-summary").value,
        evidence: $("#inc-evidence").value,
        child_impact: $("#inc-impact").value,
        confidence: Number($("#inc-conf").value),
      }),
    });
    if (data.error) { $("#inc-err").textContent = data.error; return; }
    $("#inc-summary").value = ""; $("#inc-evidence").value = ""; $("#inc-impact").value = "";
    refreshIncidents();
  });

  $("#for-hash").addEventListener("click", async () => {
    const body = {
      path: $("#for-path").value || undefined,
      content_b64: $("#for-b64").value || undefined,
      file_name: $("#for-name").value || undefined,
      summary: "local file hash",
    };
    const data = await api("/api/forensics/hash", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    $("#for-out").textContent = JSON.stringify(data, null, 2);
    if (data.sha256) $("#for-expected").value = data.sha256;
  });

  $("#for-reverify").addEventListener("click", async () => {
    const body = {
      path: $("#for-path").value || undefined,
      content_b64: $("#for-b64").value || undefined,
      expected: $("#for-expected").value,
    };
    const data = await api("/api/forensics/verify", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    $("#for-out").textContent = JSON.stringify(data, null, 2);
  });

  $("#j-save").addEventListener("click", async () => {
    $("#j-err").textContent = "";
    const data = await api("/api/journal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        summary: $("#j-summary").value,
        evidence: $("#j-evidence").value,
        child_impact: $("#j-impact").value,
        file_sha256: $("#j-hash").value || undefined,
        private_note: $("#j-private").value || undefined,
      }),
    });
    if (data.error) { $("#j-err").textContent = data.error; return; }
    $("#j-summary").value = ""; $("#j-evidence").value = ""; $("#j-impact").value = "";
    $("#j-private").value = ""; $("#j-hash").value = "";
    refreshJournal();
  });

  function filingFields() {
    return {
      state: $("#f-state").value,
      court_name: $("#f-court").value,
      petitioner: $("#f-pet").value,
      respondent: $("#f-resp").value,
      cause_no: $("#f-cause").value,
      party_role: $("#f-role").value,
      title: $("#f-title").value,
      body: $("#f-body").value,
      exhibit_count: Number($("#f-ex").value),
      party: $("#f-party").value,
    };
  }

  async function exportFiling(fmt) {
    const data = await api("/api/filing/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...filingFields(), format: fmt }),
    });
    $("#f-out").textContent = data.content || JSON.stringify(data, null, 2);
  }
  $("#f-txt").addEventListener("click", () => exportFiling("txt"));
  $("#f-html").addEventListener("click", () => exportFiling("html"));

  $$("[data-tool]").forEach((b) => b.addEventListener("click", async () => {
    const name = b.getAttribute("data-tool");
    let payload = {};
    if (name === "codelock") payload = { source: $("#cl-source").value, acknowledgment: $("#cl-ack").value };
    if (name === "shadowlock") payload = { jsonl: $("#sl-jsonl").value };
    if (name === "godlock") payload = { text: $("#gl-text").value };
    if (name === "staticclock") payload = { geo: $("#sc-geo").value };
    const data = await api("/api/tools/" + name, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    $("#tools-out").textContent = JSON.stringify(data, null, 2);
  }));

  $("#v-run").addEventListener("click", async () => {
    const data = await api("/api/verify", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonl: $("#v-jsonl").value }),
    });
    $("#v-verdict").textContent = data.verdict || "";
    $("#v-verdict").className = "verdict " + ((data.verdict || "").toLowerCase());
    $("#v-out").textContent = JSON.stringify(data, null, 2);
  });
  $("#v-local").addEventListener("click", async () => {
    const data = await api("/api/verify", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonl: "" }),
    });
    $("#v-verdict").textContent = data.verdict || "";
    $("#v-verdict").className = "verdict " + ((data.verdict || "").toLowerCase());
    $("#v-out").textContent = JSON.stringify(data, null, 2);
  });

  $("#lk-set").addEventListener("click", async () => {
    const data = await api("/api/lock/set", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase: $("#lk-pass").value }),
    });
    $("#lk-out").textContent = JSON.stringify(data, null, 2);
    refreshLock();
  });
  $("#lk-unlock").addEventListener("click", async () => {
    const data = await api("/api/lock/unlock", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase: $("#lk-pass").value }),
    });
    $("#lk-out").textContent = JSON.stringify(data, null, 2);
    refreshLock();
  });
  $("#lk-clear").addEventListener("click", async () => {
    const data = await api("/api/lock/clear", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase: $("#lk-pass").value }),
    });
    $("#lk-out").textContent = JSON.stringify(data, null, 2);
    refreshLock();
  });
  $("#ov-unlock").addEventListener("click", async () => {
    const data = await api("/api/lock/unlock", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase: $("#ov-pass").value }),
    });
    if (data.ok) { $("#ov-err").textContent = ""; refreshLock(); refreshHome(); }
    else $("#ov-err").textContent = "Passphrase did not match.";
  });

  const start = (location.hash || "#home").replace("#", "") || "home";
  show(start);
  refreshLock().then(() => { refreshHome(); });
})();
