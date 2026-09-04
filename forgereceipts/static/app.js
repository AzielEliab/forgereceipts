
(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const MAX_FILE = 12 * 1024 * 1024;
  const MODE_ALIASES = {
    home: "log",
    incident: "log",
    receipts: "io",
    filing: "file",
    import: "io",
    export: "io",
    tools: "doctor",
    lock: "doctor",
  };

  let selectedHash = null;
  let lastReceipts = [];
  let catalog = [];
  let currentLegal = null;
  let selectedTags = [];

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text, status: res.status }; }
    data._status = res.status;
    return data;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function show(mode) {
    const next = MODE_ALIASES[mode] || mode;
    $$("[data-panel]").forEach((el) => el.classList.toggle("hidden", el.getAttribute("data-panel") !== next));
    $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.mode === next));
    history.replaceState(null, "", "#" + next);
  }

  function fillStateSelect(filter) {
    const sel = $("#state-select");
    const q = (filter || "").trim().toLowerCase();
    const groups = [
      { label: "Federal / national", kind: "federal" },
      { label: "States", kind: "state" },
      { label: "District of Columbia", kind: "district" },
      { label: "Territories", kind: "territory" },
    ];
    const current = sel.value;
    sel.innerHTML = "";
    groups.forEach((g) => {
      const rows = catalog.filter((j) => j.kind === g.kind).filter((j) => {
        if (!q) return true;
        return (j.name + " " + j.id).toLowerCase().includes(q);
      });
      if (!rows.length) return;
      const og = document.createElement("optgroup");
      og.label = g.label;
      rows.forEach((j) => {
        const opt = document.createElement("option");
        opt.value = j.id;
        opt.textContent = j.id === "US" ? j.name : (j.id + " — " + j.name);
        og.appendChild(opt);
      });
      sel.appendChild(og);
    });
    if ([].some.call(sel.options, (o) => o.value === current)) sel.value = current;
  }

  function receiptCard(r) {
    const div = document.createElement("div");
    div.className = "receipt" + (r.hash && r.hash === selectedHash ? " active" : "");
    div.dataset.hash = r.hash || "";
    div.innerHTML = `<strong>${escapeHtml(r.summary || r.file_name || "Receipt")}</strong>
      <div class="muted">${escapeHtml(r.timestamp || "")} · ${escapeHtml(r.kind || "")}</div>
      <div class="hash">${escapeHtml(r.hash || "")}</div>`;
    div.addEventListener("click", () => {
      selectedHash = r.hash;
      renderDetail(r);
      $$(".receipt").forEach((el) => el.classList.toggle("active", el.dataset.hash === selectedHash));
    });
    return div;
  }

  function renderDetail(r) {
    const html = `<p><strong>${escapeHtml(r.summary || r.file_name || "Receipt")}</strong></p>
      <p>This is the saved receipt for this file.</p>
      <p class="hash">${escapeHtml(r.hash || "")}</p>
      ${r.child_impact ? `<p><em>Child impact:</em> ${escapeHtml(r.child_impact)}</p>` : ""}
      <p class="muted">Not legal advice. A receipt is not legal proof.</p>`;
    ["#home-detail", "#inc-detail"].forEach((sel) => {
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

  function renderTags(legal) {
    const box = $("#log-tags");
    box.innerHTML = "";
    const tags = (legal && legal.state && legal.state.legal_tags) || [];
    tags.forEach((t) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = t.label;
      b.classList.toggle("on", selectedTags.includes(t.label));
      b.addEventListener("click", () => {
        if (selectedTags.includes(t.label)) {
          selectedTags = selectedTags.filter((x) => x !== t.label);
        } else {
          selectedTags.push(t.label);
        }
        renderTags(legal);
      });
      box.appendChild(b);
    });
  }

  function renderScore(score) {
    const el = $("#log-score");
    const sway = score.sway || {};
    const move = score.next_best_move || {};
    const flags = score.flags || [];
    el.innerHTML = `<div class="score">${escapeHtml(String(score.score ?? "—"))}</div>
      <p class="muted">Pattern Strength Score — a local count, not a win chance.</p>
      <div class="bar"><span style="width:${Math.max(0, Math.min(100, score.score || 0))}%"></span></div>
      <p><strong>Next:</strong> ${escapeHtml(move.plain || "")}</p>
      <p><strong>Balance:</strong> ${escapeHtml(sway.label || "")}</p>
      <ul>${flags.map((f) => `<li>${escapeHtml(f.plain)}</li>`).join("")}</ul>
      <p class="muted">${escapeHtml(score.disclaimer || "")}</p>`;
  }

  async function refreshLock() {
    const st = await api("/api/lock");
    const overlay = $("#lock-overlay");
    if (st.lock_set && !st.unlocked) overlay.classList.remove("hidden");
    else overlay.classList.add("hidden");
    $("#lk-out").textContent = JSON.stringify(st, null, 2);
    return st;
  }

  async function refreshLegal(jid) {
    const legal = await api("/api/legal" + (jid ? ("?jurisdiction=" + encodeURIComponent(jid)) : ""));
    currentLegal = legal;
    const name = (legal.state && legal.state.name) || (legal.jurisdiction && legal.jurisdiction.name) || "your state";
    $("#state-name").textContent = name;
    if (legal.jurisdiction && legal.jurisdiction.id) {
      $("#state-select").value = legal.jurisdiction.id;
    }
    renderTags(legal);
    return legal;
  }

  async function refreshReceipts() {
    const data = await api("/api/receipts");
    lastReceipts = data.receipts || [];
    const list = $("#home-list");
    if (list) {
      list.innerHTML = "";
      lastReceipts.slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
    }
    if (selectedHash) {
      const row = lastReceipts.find((r) => r.hash === selectedHash);
      if (row) renderDetail(row);
    }
  }

  async function refreshLog() {
    const data = await api("/api/receipts?kind=incident");
    const list = $("#inc-list");
    list.innerHTML = "";
    (data.receipts || []).slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
    const score = await api("/api/score");
    renderScore(score);
  }

  async function refreshJournal() {
    const data = await api("/api/receipts?kind=journal");
    const list = $("#j-list");
    list.innerHTML = "";
    (data.receipts || []).slice().reverse().forEach((r) => list.appendChild(receiptCard(r)));
  }

  async function refreshFiling() {
    const t = await api("/api/filing");
    if (t.caption_placeholders && t.caption_placeholders.state) {
      $("#f-state").value = t.caption_placeholders.state;
    }
    if (t.exhibit) {
      $("#f-party").options[0].text = t.exhibit.petitioner || "Petitioner's Exhibit 1, 2, 3…";
      $("#f-party").options[1].text = t.exhibit.respondent || "Respondent's Exhibit A, B, C…";
    }
    const efile = t.efiling || {};
    $("#file-efile").textContent = (efile.odyssey ? "Odyssey note: " : "E-filing note: ") + (efile.note || t.note || "");
    $("#f-check").innerHTML = `<p class="help">${escapeHtml(t.disclaimer || "")}</p>
      <ol>${(t.efiling_checklist || []).map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ol>`;
  }

  async function refreshGuide() {
    const g = await api("/api/guide");
    $("#guide-honesty").textContent = g.honesty || "";
    const fed = (g.topics || []).filter((t) => t.scope === "federal");
    const rest = (g.topics || []).filter((t) => t.scope !== "federal");
    $("#guide-federal").innerHTML = `<h3>Federal / national (always on)</h3>
      ${(g.baseline || []).map((b) => `<div class="blurb"><strong>${escapeHtml(b.name)}</strong> <span class="muted">${escapeHtml(b.cite)}</span><p>${escapeHtml(b.blurb)}</p></div>`).join("")}
      ${fed.map((t) => `<p><strong>${escapeHtml(t.title)}</strong> — ${escapeHtml(t.body)}</p>`).join("")}`;
    $("#guide-topics").innerHTML = rest.map((t) => `<div class="guide-card"><h3>${escapeHtml(t.title)}</h3><p>${escapeHtml(t.body)}</p></div>`).join("");
  }

  async function applyState(code) {
    const saved = await api("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jurisdiction: code }),
    });
    if (saved.error) return;
    selectedTags = [];
    await refreshLegal(saved.jurisdiction);
    await refreshFiling();
    await refreshGuide();
  }

  $$("#nav button").forEach((b) => b.addEventListener("click", () => {
    const mode = b.dataset.mode;
    show(mode);
    if (mode === "log") refreshLog();
    if (mode === "journal") refreshJournal();
    if (mode === "file") refreshFiling();
    if (mode === "guide") refreshGuide();
    if (mode === "io") refreshReceipts();
    if (mode === "doctor") refreshLock();
  }));

  $("#state-filter").addEventListener("input", (ev) => fillStateSelect(ev.target.value));
  $("#state-select").addEventListener("change", (ev) => applyState(ev.target.value));
  $("#btn-doctor").addEventListener("click", () => {
    show("doctor");
    refreshLock();
  });

  $("#log-save").addEventListener("click", async () => {
    $("#inc-err").textContent = "";
    const extra = selectedTags.length ? ("\nTags: " + selectedTags.join("; ")) : "";
    const data = await api("/api/incident", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        summary: $("#inc-summary").value,
        evidence: ($("#inc-evidence").value || "") + extra,
        child_impact: $("#inc-impact").value,
        confidence: Number($("#inc-conf").value),
      }),
    });
    if (data.error) { $("#inc-err").textContent = data.error; return; }
    $("#inc-summary").value = ""; $("#inc-evidence").value = ""; $("#inc-impact").value = "";
    selectedTags = [];
    renderTags(currentLegal);
    refreshLog();
  });

  $("#j-file").addEventListener("change", async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    try {
      const b64 = await fileToB64(file);
      const data = await api("/api/forensics/hash", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_b64: b64,
          file_name: file.name,
          summary: "journal file hash",
          child_impact: "Hashed a file already on this computer for a Time with Child note.",
        }),
      });
      if (data.sha256) $("#j-hash").value = data.sha256;
    } catch (err) {
      $("#j-err").textContent = err.message || String(err);
    }
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
    $("#j-private").value = ""; $("#j-hash").value = ""; $("#j-file").value = "";
    refreshJournal();
  });

  $("#for-pick").addEventListener("click", async () => {
    if ($("#for-path").value) {
      const data = await api("/api/forensics/hash", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: $("#for-path").value,
          file_name: $("#for-name").value || undefined,
          summary: "local file hash",
        }),
      });
      $("#for-out").textContent = JSON.stringify(data, null, 2);
      if (data.sha256) $("#for-expected").value = data.sha256;
      return;
    }
    $("#for-file").click();
  });
  $("#for-file").addEventListener("change", async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    ev.target.value = "";
    if (!file) return;
    try {
      const b64 = await fileToB64(file);
      $("#for-name").value = file.name;
      const data = await api("/api/forensics/hash", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content_b64: b64, file_name: file.name, summary: "local file hash" }),
      });
      $("#for-out").textContent = JSON.stringify(data, null, 2);
      if (data.sha256) $("#for-expected").value = data.sha256;
    } catch (err) {
      $("#for-out").textContent = err.message || String(err);
    }
  });

  $("#for-reverify").addEventListener("click", async () => {
    const body = {
      path: $("#for-path").value || undefined,
      expected: $("#for-expected").value,
    };
    const data = await api("/api/forensics/verify", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    $("#for-out").textContent = JSON.stringify(data, null, 2);
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
      jurisdiction: $("#state-select").value,
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
    if (data.ok) { $("#ov-err").textContent = ""; refreshLock(); refreshLog(); }
    else $("#ov-err").textContent = "Password did not match.";
  });

  $("#doc-run").addEventListener("click", async () => {
    const data = await api("/api/doctor");
    $("#doc-plain").textContent = data.plain || "";
    $("#doc-list").innerHTML = (data.checks || []).map((c) =>
      `<p><strong>${escapeHtml(c.verdict)}</strong> ${escapeHtml(c.plain)}</p>`
    ).join("");
    $("#doc-out").classList.remove("hidden");
    $("#doc-out").textContent = JSON.stringify(data, null, 2);
  });

  async function boot() {
    const cat = await api("/api/jurisdictions");
    catalog = cat.jurisdictions || [];
    const meta = await api("/api/meta");
    fillStateSelect("");
    if (meta.jurisdiction) $("#state-select").value = meta.jurisdiction;
    await refreshLegal(meta.jurisdiction);
    const start = MODE_ALIASES[(location.hash || "#log").replace("#", "")] || (location.hash || "#log").replace("#", "") || "log";
    show(start);
    await refreshLock();
    if (start === "log") await refreshLog();
    if (start === "io") await refreshReceipts();
    if (start === "journal") await refreshJournal();
    if (start === "file") await refreshFiling();
    if (start === "guide") await refreshGuide();
  }

  boot();
})();
