
(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const MAX_FILE = 12 * 1024 * 1024;
  let selectedHash = null;
  let lastReceipts = [];
  let viewMode = localStorage.getItem("forgereceipts.view") || "simple";

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text, status: res.status }; }
    data._status = res.status;
    return data;
  }

  function applyView() {
    document.body.classList.toggle("simple", viewMode === "simple");
    document.body.classList.toggle("advanced", viewMode === "advanced");
    $$("#view-toggle button").forEach((b) => b.classList.toggle("active", b.dataset.view === viewMode));
    localStorage.setItem("forgereceipts.view", viewMode);
  }

  function show(mode) {
    $$("[data-panel]").forEach((el) => el.classList.toggle("hidden", el.getAttribute("data-panel") !== mode));
    $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
    history.replaceState(null, "", "#" + mode);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function receiptCard(r) {
    const div = document.createElement("div");
    div.className = "receipt" + (r.hash && r.hash === selectedHash ? " active" : "");
    div.dataset.hash = r.hash || "";
    const impact = r.child_impact ? `<div><em>Child impact:</em> ${escapeHtml(r.child_impact)}</div>` : "";
    const priv = r.private_note ? `<div><em>Private note:</em> ${escapeHtml(r.private_note)}</div>` : "";
    const file = r.file_sha256 ? `<div class="hash">file ${escapeHtml(r.file_name || "")} ${escapeHtml(r.file_sha256)}</div>` : "";
    const extra = viewMode === "advanced"
      ? `${impact}${priv}${file}<div class="hash">${escapeHtml(r.hash || "")}</div>`
      : `<div class="hash">${escapeHtml(r.hash || "")}</div>`;
    div.innerHTML = `<strong>${escapeHtml(r.summary || r.file_name || "Receipt")}</strong>
      <div class="muted">${escapeHtml(r.timestamp || "")} · ${escapeHtml(r.kind || "")}</div>
      ${extra}`;
    div.addEventListener("click", () => {
      selectedHash = r.hash;
      renderDetail(r);
      $$(".receipt").forEach((el) => el.classList.toggle("active", el.dataset.hash === selectedHash));
    });
    return div;
  }

  function renderDetail(r) {
    const simple = `<p><strong>${escapeHtml(r.summary || r.file_name || "Receipt")}</strong></p>
      <p>This is the saved receipt for this file.</p>
      <p class="hash">${escapeHtml(r.hash || "")}</p>
      <p class="muted">Not legal advice. A receipt is not legal proof.</p>`;
    const advanced = `<p><strong>${escapeHtml(r.summary || "")}</strong></p>
      <div class="muted">${escapeHtml(r.timestamp || "")} · ${escapeHtml(r.kind || "")} · conf ${r.confidence}</div>
      ${r.child_impact ? `<p><em>Child impact:</em> ${escapeHtml(r.child_impact)}</p>` : ""}
      ${r.file_sha256 ? `<p class="hash">file ${escapeHtml(r.file_name || "")}<br>${escapeHtml(r.file_sha256)}</p>` : ""}
      <p class="hash">hash ${escapeHtml(r.hash || "")}</p>
      <p class="hash">prev ${escapeHtml(r.prev_hash || "")}</p>
      <pre class="out">${escapeHtml(JSON.stringify(r, null, 2))}</pre>
      <p class="muted">Not legal advice. A receipt is not legal proof.</p>`;
    const html = viewMode === "advanced" ? advanced : simple;
    ["#home-detail", "#rec-detail"].forEach((sel) => {
      const el = $(sel);
      if (!el) return;
      el.innerHTML = html;
      el.classList.remove("hidden");
    });
  }

  function showSaved(data) {
    const box = $("#saved-box");
    box.classList.remove("hidden");
    $("#saved-hash").textContent = data.sha256 || data.hash || (data.receipt && data.receipt.hash) || "";
    $("#saved-note").textContent = (data.plain || "Saved a receipt for this file") + "  Not legal advice. A receipt is not legal proof.";
    $("#home-err").textContent = "";
  }

  function fileToB64(file) {
    return new Promise((resolve, reject) => {
      if (file.size > MAX_FILE) {
        reject(new Error("That file is too big. ForgeReceipts only takes files up to 12 MB."));
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const s = String(reader.result || "");
        const i = s.indexOf(",");
        resolve(i >= 0 ? s.slice(i + 1) : s);
      };
      reader.onerror = () => reject(new Error("That file could not be read. Try another file."));
      reader.readAsDataURL(file);
    });
  }

  function downloadText(filename, text) {
    const blob = new Blob([text], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
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
    await refreshReceipts();
  }

  async function refreshReceipts() {
    const data = await api("/api/receipts");
    lastReceipts = data.receipts || [];
    ["#home-list", "#rec-list"].forEach((sel) => {
      const list = $(sel);
      if (!list) return;
      list.innerHTML = "";
      lastReceipts.slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
    });
    if (selectedHash) {
      const row = lastReceipts.find((r) => r.hash === selectedHash);
      if (row) renderDetail(row);
    }
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
    if (mode === "receipts") refreshReceipts();
    if (mode === "incident") refreshIncidents();
    if (mode === "journal") refreshJournal();
    if (mode === "filing") refreshFiling();
    if (mode === "lock") refreshLock();
  }));

  $$("#view-toggle button").forEach((b) => b.addEventListener("click", () => {
    viewMode = b.dataset.view;
    applyView();
    refreshReceipts();
  }));

  $("#btn-add-file").addEventListener("click", () => $("#add-file-input").click());
  $("#add-file-input").addEventListener("change", async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    ev.target.value = "";
    if (!file) return;
    $("#home-err").textContent = "";
    try {
      const b64 = await fileToB64(file);
      const data = await api("/api/forensics/hash", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content_b64: b64, file_name: file.name, summary: "local file hash" }),
      });
      if (data.error) { $("#home-err").textContent = data.error; return; }
      selectedHash = data.receipt && data.receipt.hash;
      showSaved(data);
      refreshReceipts();
    } catch (err) {
      $("#home-err").textContent = err.message || String(err);
    }
  });

  $("#btn-import").addEventListener("click", () => $("#import-file-input").click());
  $("#import-file-input").addEventListener("change", async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    ev.target.value = "";
    if (!file) return;
    $("#home-err").textContent = "";
    try {
      const text = await file.text();
      const data = await api("/api/receipt/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ json: text }),
      });
      if (data.error || data.ok === false) {
        $("#home-err").textContent = data.error || data.plain || "This receipt does not match its hash.";
        return;
      }
      selectedHash = data.receipt && data.receipt.hash;
      showSaved({ ...data, sha256: data.receipt && (data.receipt.imported_hash || data.receipt.hash) });
      refreshReceipts();
    } catch (err) {
      $("#home-err").textContent = err.message || String(err);
    }
  });

  $("#btn-export").addEventListener("click", async () => {
    $("#home-err").textContent = "";
    const body = selectedHash ? { hash: selectedHash } : {};
    const data = await api("/api/receipt/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (data.error) { $("#home-err").textContent = data.error; return; }
    downloadText(data.filename || "receipt.json", data.content || "");
    $("#saved-box").classList.remove("hidden");
    $("#saved-hash").textContent = data.filename || "";
    $("#saved-note").textContent = data.plain || "Copied this receipt into a file you can keep.";
  });

  $("#btn-demo").addEventListener("click", async () => {
    $("#home-err").textContent = "";
    const data = await api("/api/demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (data.error) { $("#home-err").textContent = data.error; return; }
    selectedHash = data.receipt && data.receipt.hash;
    showSaved(data);
    refreshReceipts();
  });

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

  applyView();
  const start = (location.hash || "#home").replace("#", "") || "home";
  show(start);
  refreshLock().then(() => { refreshHome(); });
})();
