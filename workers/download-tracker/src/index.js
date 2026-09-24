import { handleRuntime } from "./runtime.js";
import { handleMesh } from "./mesh.js";
import { classifyRequest, readBotManagement } from "./classify.js";
import {
  isolatedKeys,
  isReservedCounterKey,
  shapeCountBody,
  shapeHumanBotFields,
} from "./stats-shape.js";

/**
 * ForgeReceipts download tracker (Cloudflare Worker).
 *
 * GET  /download?repo=AzielEliab/forgereceipts&tag=latest&asset=...
 *      increments KV, 302 to the GitHub release asset
 *      (default https://github.com/AzielEliab/forgereceipts/releases)
 * GET  /count   JSON {project, views, downloads, total} — total = downloads (azhub convention)
 * GET  /stats   JSON totals + per-repo + per-branch breakdown
 * GET/POST /v1/mesh/*  PROXY suite mesh to aziel-runtime (does not increment)
 * POST /event   forks report a download {owner,repo,branch,fork,asset}
 *
 * KV binding DOWNLOADS. Keys: project|owner|repo|branch|fork
 * CORS *. No secrets in this tree.
 */

const PROJECT = "forgereceipts";
const KEYS = isolatedKeys(PROJECT);

const DEFAULT_ASSET = "forgereceipts-0.3.0.tar.gz";
const DEFAULT_OWNER = "AzielEliab";
const DEFAULT_REPO = "forgereceipts";
const DEFAULT_BRANCH = "main";
const HOST = "https://forgereceipts-download-tracker.vibelock.workers.dev";
const GITHUB_REPO = "https://github.com/AzielEliab/forgereceipts";

const GITHUB_RELEASES = "https://github.com/AzielEliab/forgereceipts/releases";
const GITHUB_LATEST = "https://github.com/AzielEliab/forgereceipts/releases/latest";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, User-Agent",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function redirect(url) {
  return new Response(null, {
    status: 302,
    headers: { Location: url, ...corsHeaders() },
  });
}

function splitOwnerRepo(value, fallbackOwner, fallbackRepo) {
  if (typeof value === "string" && value.includes("/")) {
    const [o, r] = value.split("/").filter(Boolean);
    if (o && r) return { owner: o, repo: r };
  }
  return { owner: fallbackOwner, repo: fallbackRepo };
}

function parseDims(src) {
  const get = (k) => {
    if (src == null) return null;
    if (typeof src.get === "function") {
      const v = src.get(k);
      return v == null || v === "" ? null : v;
    }
    const v = src[k];
    return v == null || v === "" ? null : v;
  };

  let owner = get("owner") || DEFAULT_OWNER;
  let repo = get("repo") || DEFAULT_REPO;
  if (typeof repo === "string" && repo.includes("/")) {
    const split = splitOwnerRepo(repo, owner, DEFAULT_REPO);
    owner = split.owner;
    repo = split.repo;
  }

  const branch = get("branch") || DEFAULT_BRANCH;
  const tag = get("tag") || "latest";
  const asset = get("asset") || "";

  const forkRaw = get("fork");
  let fork = "0";
  if (forkRaw === 1 || forkRaw === true || forkRaw === "1" || forkRaw === "true") {
    fork = "1";
  } else if (typeof forkRaw === "string" && forkRaw.includes("/")) {
    const split = splitOwnerRepo(forkRaw, owner, repo);
    owner = split.owner;
    repo = split.repo;
    fork = "1";
  } else if (forkRaw != null && forkRaw !== 0 && forkRaw !== false && forkRaw !== "0" && forkRaw !== "false") {
    fork = "1";
  }

  if (`${owner}/${repo}`.toLowerCase() !== `${DEFAULT_OWNER}/${DEFAULT_REPO}`.toLowerCase()) {
    fork = "1";
  }

  return { project: PROJECT, owner, repo, branch, fork, tag, asset };
}

function kvKey(dims) {
  return `${dims.project}|${dims.owner}|${dims.repo}|${dims.branch}|${dims.fork}`;
}

function githubAssetUrl(owner, repo, tag, asset) {
  if (!asset) {
    if (owner === DEFAULT_OWNER && repo === DEFAULT_REPO) return GITHUB_RELEASES;
    return `https://github.com/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/releases`;
  }
  if (!tag || tag === "latest") {
    return `https://github.com/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/releases/latest/download/${encodeURIComponent(asset)}`;
  }
  return `https://github.com/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/releases/download/${encodeURIComponent(tag)}/${encodeURIComponent(asset)}`;
}


async function bump(env, key) {
  const n = parseInt((await env.DOWNLOADS.get(key)) || "0", 10) + 1;
  await env.DOWNLOADS.put(key, String(n));
  return n;
}

async function incrementSplit(env, humanKey, botKey, request) {
  const cls = classifyRequest(request);
  const splitKey = cls.bucket === "human" ? humanKey : botKey;
  await bump(env, splitKey);
  return cls;
}

async function readHumanBotSplit(env, request) {
  const views = parseInt((await env.DOWNLOADS.get(KEYS.views)) || "0", 10) || 0;
  const downloadsRaw = await env.DOWNLOADS.get(KEYS.total);
  let downloads = parseInt(downloadsRaw || "0", 10);
  if (!Number.isFinite(downloads) || downloads < 0) downloads = 0;
  const viewsHuman = parseInt((await env.DOWNLOADS.get(KEYS.views_human)) || "0", 10) || 0;
  const downloadsHuman = parseInt((await env.DOWNLOADS.get(KEYS.downloads_human)) || "0", 10) || 0;
  const botManagementAvailable = readBotManagement(request).available;
  return shapeHumanBotFields({
    views,
    downloads,
    views_human: viewsHuman,
    downloads_human: downloadsHuman,
    botManagementAvailable,
  });
}

function enrichStatsWithHumanBot(stats, split) {
  return {
    ...stats,
    views_human: split.views_human,
    views_bot: split.views_bot,
    downloads_human: split.downloads_human,
    downloads_bot: split.downloads_bot,
    human: split.human,
    bot: split.bot,
    classification: split.classification,
  };
}

async function increment(env, dims, request) {
  const key = kvKey(dims);
  const n = parseInt((await env.DOWNLOADS.get(key)) || "0", 10) + 1;
  await env.DOWNLOADS.put(key, String(n));
  if (request) await incrementSplit(env, KEYS.downloads_human, KEYS.downloads_bot, request);

  return n;
}

async function listAllKeys(env) {
  const keys = [];
  let cursor;
  do {
    const page = await env.DOWNLOADS.list(cursor ? { cursor } : {});
    keys.push(...page.keys);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return keys;
}

async function collectStats(env, request) {
  const keys = await listAllKeys(env);
  let total = 0;
  const by_repo = {};
  const by_branch = {};
  const by_fork = { "0": 0, "1": 0 };
  const breakdown = [];

  for (const k of keys) {
    const name = k.name;
    if (isReservedCounterKey(name, PROJECT)) continue;
    const n = parseInt((await env.DOWNLOADS.get(name)) || "0", 10);
    if (!Number.isFinite(n) || n <= 0) continue;
    const parts = name.split("|");
    if (parts.length < 5) continue;
    const [project, owner, repo, branch, fork] = parts;
    total += n;
    const repoId = `${owner}/${repo}`;
    by_repo[repoId] = (by_repo[repoId] || 0) + n;
    by_branch[branch] = (by_branch[branch] || 0) + n;
    const forkFlag = fork === "1" ? "1" : "0";
    by_fork[forkFlag] = (by_fork[forkFlag] || 0) + n;
    breakdown.push({ project, owner, repo, branch, fork: forkFlag, count: n });
  }

  const views = parseInt((await env.DOWNLOADS.get(viewsKey())) || "0", 10) || 0;
  const shown = total;
  const __hbViews = parseInt((await env.DOWNLOADS.get(KEYS.views)) || "0", 10) || 0;
  const __hbViewsHuman = parseInt((await env.DOWNLOADS.get(KEYS.views_human)) || "0", 10) || 0;
  const __hbDownloadsHuman = parseInt((await env.DOWNLOADS.get(KEYS.downloads_human)) || "0", 10) || 0;
  const __hbBotMgmt = request ? readBotManagement(request).available : false;

  return {
    ...shapeHumanBotFields({
      views: (typeof views !== 'undefined' ? views : __hbViews),
      downloads: (typeof downloads !== 'undefined' ? downloads : (typeof shown !== 'undefined' ? shown : (typeof total !== 'undefined' ? total : 0))),
      views_human: __hbViewsHuman,
      downloads_human: __hbDownloadsHuman,
      botManagementAvailable: __hbBotMgmt,
    }),

    project: PROJECT,
    total: shown,
    views,
    downloads: shown,
    by_repo,
    by_branch,
    by_fork,
    breakdown,
    note: "Forks identified by GitHub owner/repo. Key layout: project|owner|repo|branch|fork. Views are separate from downloads. /v1 does not increment.",
  };
}


function viewsKey() {
  return PROJECT + "|__views__";
}

async function incrementViews(env, request) {
  const n = parseInt((await env.DOWNLOADS.get(viewsKey())) || "0", 10) + 1;
  await env.DOWNLOADS.put(viewsKey(), String(n));
  if (request) await incrementSplit(env, KEYS.views_human, KEYS.views_bot, request);

  return n;
}

function installScript() {
  return `#!/usr/bin/env bash
# ForgeReceipts one-click install. Counted download via this Worker.
set -euo pipefail
HOST="${HOST}"
ASSET="${DEFAULT_ASSET}"
WORKDIR="\${FORGERECEIPTS_HOME:-\$HOME/forgereceipts}"
mkdir -p "\$WORKDIR"
cd "\$WORKDIR"
echo "Downloading counted tarball from \${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "\${HOST}/download?asset=\${ASSET}" -o "\${ASSET}"
tar -xzf "\${ASSET}"
DIR="\$(find . -maxdepth 1 -type d -name 'forgereceipts-*' | head -n 1)"
if [ -n "\${DIR}" ]; then
  cd "\${DIR}"
fi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
echo
echo "Installed ForgeReceipts."
echo "Run:  forgereceipts ui"
echo "Then open http://127.0.0.1:8787  (loopback only)"
echo "Author: Aziel Eliab."
`;
}

async function serveAsset(request, env, asset, { head = false } = {}) {
  if (!env.ASSETS) {
    return json({ error: "assets binding missing" }, 500);
  }
  const assetUrl = new URL("/" + asset, request.url);
  const assetRes = await env.ASSETS.fetch(new Request(assetUrl, { method: "GET" }));
  if (!assetRes.ok) {
    return json({ error: "asset not hosted", asset, status: assetRes.status }, 404);
  }
  const headers = new Headers();
  headers.set("Content-Type", "application/gzip");
  headers.set("Content-Disposition", 'attachment; filename="' + asset.replaceAll('"', "") + '"');
  headers.set("Cache-Control", "private, no-store");
  const len = assetRes.headers.get("Content-Length");
  if (len) headers.set("Content-Length", len);
  for (const [k, v] of Object.entries(corsHeaders())) headers.set(k, v);
  if (head) {
    return new Response(null, { status: 200, headers });
  }
  return new Response(assetRes.body, { status: 200, headers });
}

async function indexHtml(env) {
  const stats = await collectStats(env);
  const downloads = Number(stats.downloads != null ? stats.downloads : stats.total) || 0;
  const views = parseInt((await env.DOWNLOADS.get(viewsKey())) || "0", 10) || 0;
  const v = views.toLocaleString("en-US");
  const n = downloads.toLocaleString("en-US");
  const breakdown = (stats.breakdown || [])
    .map(
      (b) =>
        `<li><code>${b.owner}/${b.repo}</code> branch <code>${b.branch}</code> fork=${b.fork} → ${b.count}</li>`,
    )
    .join("") || "<li>none yet</li>";
  return `<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ForgeReceipts — Aziel Eliab</title>
<meta name="description" content="Local-first evidence integrity platform for pro se fathers in family court, by Aziel Eliab; not legal advice.">
<meta name="author" content="Aziel Eliab">
<link rel="canonical" href="https://forgereceipts-download-tracker.vibelock.workers.dev/">
<meta property="og:title" content="ForgeReceipts — Aziel Eliab">
<meta property="og:description" content="Local-first evidence integrity platform for pro se fathers in family court, by Aziel Eliab; not legal advice.">
<meta property="og:url" content="https://forgereceipts-download-tracker.vibelock.workers.dev/">
<meta property="og:type" content="website">
<meta property="og:image" content="https://forgereceipts-download-tracker.vibelock.workers.dev/sigil.png">
<meta property="og:image:alt" content="rose-star brand mark">
<link rel="icon" href="/sigil.png">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "ForgeReceipts",
  "author": {
    "@type": "Person",
    "name": "Aziel Eliab"
  },
  "codeRepository": "https://github.com/AzielEliab/forgereceipts",
  "downloadUrl": "https://forgereceipts-download-tracker.vibelock.workers.dev/download",
  "license": "https://www.apache.org/licenses/LICENSE-2.0",
  "url": "https://forgereceipts-download-tracker.vibelock.workers.dev/",
  "description": "Local-first evidence integrity platform for pro se fathers in family court, by Aziel Eliab; not legal advice.",
  "identifier": "https://doi.org/10.5281/zenodo.21436074"
}
</script>
<!-- gitbaby-seo -->
<style>
  :root {
    color-scheme: dark;
    --bg: #101114;
    --text: #f3f4f6;
    --muted: #c5ccd6;
    --panel: #181b22;
    --line: #3c4454;
    --fill: #f4f5f7;
    --ink: #12141a;
    --focus: #ffffff;
    --banner-bg: #2c2618;
    --banner-text: #f6e7b8;
    --link: #d7e0fb;
    --accent: #f0d48a;
    --code-bg: #0d0f13;
  }
  @media (prefers-color-scheme: dark) {
    :root { color-scheme: dark; }
  }
  @media (prefers-color-scheme: light) {
    :root {
      color-scheme: light;
      --bg: #f7f6f3;
      --text: #161616;
      --muted: #3e4450;
      --panel: #ffffff;
      --line: #c8c4ba;
      --fill: #161616;
      --ink: #ffffff;
      --focus: #0b3a82;
      --banner-bg: #f4ead0;
      --banner-text: #3a2e10;
      --link: #1a3f8a;
      --accent: #5c4308;
      --code-bg: #efeee9;
    }
  }
  * { box-sizing: border-box; }
  html { background: var(--bg); }
  body {
    font: 16px/1.5 system-ui, "Segoe UI", sans-serif;
    max-width: 40rem;
    margin: 0 auto;
    padding: 1.15rem 1rem 2.75rem;
    background: var(--bg);
    color: var(--text);
    overflow-wrap: anywhere;
  }
  a.skip { position: absolute; left: -999px; top: 0; }
  a.skip:focus {
    left: 1rem; top: 1rem; z-index: 5;
    background: var(--fill); color: var(--ink);
    padding: .45rem .75rem; text-decoration: none;
    outline: 2px solid var(--focus); outline-offset: 2px;
  }
  a:focus-visible, button:focus-visible, input:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }
  .hero { margin: 0 0 1.25rem; }
  .brandrow { display: flex; align-items: center; margin: 0 0 .85rem; min-height: 48px; }
  .brandmark { width: 40px; height: 40px; border-radius: 10px; object-fit: cover; flex: 0 0 40px; box-shadow: 0 0 0 1px var(--line); }
  h1 { font-size: 2rem; font-weight: 700; letter-spacing: .01em; line-height: 1.15; margin: 0 0 .35rem; }
  .motto { color: var(--muted); margin: 0 0 .7rem; font-size: 1.05rem; }
  .lede { margin: 0 0 .9rem; max-width: 38rem; }
  a.btn.block.primary {
    display: block; width: 100%; margin: 0 0 .7rem; padding: 1.05rem 1.2rem;
    border: 1px solid transparent; border-radius: 10px;
    background: var(--fill); color: var(--ink);
    text-align: center; text-decoration: none;
    font: 700 1.25rem/1.15 ui-monospace, Menlo, Consolas, monospace;
    letter-spacing: .03em; cursor: pointer;
  }
  a.btn.block.primary:hover { filter: brightness(1.06); }
  .asset-note { color: var(--muted); font-size: .92rem; margin: 0 0 1rem; }
  .features { display: grid; grid-template-columns: 1fr; gap: .7rem 1.1rem; margin: 0; padding: 0; list-style: none; }
  .features li { margin: 0; }
  @media (min-width: 640px) {
    .features { grid-template-columns: 1fr 1fr 1fr; }
  }
  .banner { border: 1px solid var(--line); background: var(--banner-bg); color: var(--banner-text); padding: .85rem 1rem; border-radius: 8px; margin: 0 0 1rem; font-size: .95rem; }
  .card { border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem 1.15rem; background: var(--panel); margin: 0 0 1rem; }
  .nums { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin: 0 0 1rem; }
  .count { font-size: 2.2rem; font-variant-numeric: tabular-nums; font-weight: 700; margin: 0; }
  .count span { display: block; font-size: .95rem; font-weight: 600; color: var(--muted); }
  .kid { font-size: 1.02rem; margin: 0 0 .85rem; }
  button.btn.install {
    display: block; width: 100%; text-align: center;
    font: 600 1rem/1.2 system-ui, sans-serif;
    padding: .8rem 1rem; border-radius: 10px;
    border: 1px solid var(--line); background: transparent; color: var(--text);
    cursor: pointer;
  }
  button.btn.install.copied { background: var(--fill); color: var(--ink); border-color: transparent; }
  .meta, .iso { margin: .85rem 0 0; color: var(--muted); font-size: .92rem; }
  a { color: var(--link); }
  .meta a, .cite a, footer a { text-decoration-thickness: 1px; text-underline-offset: .15em; }
  pre {
    background: var(--code-bg); color: var(--text);
    padding: .75rem .9rem; border-radius: 8px; font-size: .82rem;
    max-width: 100%; overflow-x: auto; white-space: pre-wrap; overflow-wrap: anywhere;
  }
  code { font-size: .92em; font-family: ui-monospace, Menlo, Consolas, monospace; }
  .cite { margin: 0 0 1rem; padding-top: .25rem; }
  .cite h2, .card h2 { font-size: 1.05rem; font-weight: 700; margin: 0 0 .4rem; letter-spacing: 0; text-transform: none; color: var(--text); }
  .cite p { color: var(--muted); font-size: .95rem; }
  #meshStrip {
    border: 1px solid var(--line); border-radius: 12px; padding: .85rem 1rem;
    background: var(--panel); margin: 0 0 1rem;
    display: flex; flex-wrap: wrap; align-items: center; gap: .65rem .9rem;
    font-size: .88rem; color: var(--muted);
  }
  #meshStrip .live { color: var(--text); }
  #meshStrip .live b { color: var(--accent); font-size: 1.35rem; margin-right: .35rem; }
  #meshStrip .rollup b { color: var(--accent); }
  #meshStrip .controls { display: flex; flex-wrap: wrap; gap: .5rem; flex-basis: 100%; }
  #meshStrip button {
    font: 600 .82rem/1 system-ui, sans-serif; min-height: 2rem; padding: 0 .75rem;
    border-radius: 8px; background: transparent; color: var(--text);
    border: 1px solid var(--line); cursor: pointer;
  }
  #meshStrip button:hover { background: var(--bg); }
  #meshStrip input {
    flex: 1 1 10rem; min-width: 0; width: auto; max-width: 100%;
    padding: .45rem .6rem; border: 1px solid var(--line); border-radius: 8px;
    background: var(--bg); color: var(--text); font: inherit;
  }
  #meshProducts { flex-basis: 100%; margin: 0; overflow-wrap: anywhere; }
  footer.quiet { color: var(--muted); font-size: .9rem; padding: .35rem 0 0; }
  footer.quiet p { margin: .35rem 0; }
  footer.quiet a { color: var(--text); }
</style>
<body>
  <a class="skip" href="#downloadBtn">Skip to download</a>
  <header class="hero">
    <div class="brandrow"><img class="brandmark" src="/sigil.png" width="40" height="40" alt="" decoding="async"></div>
    <h1>ForgeReceipts</h1>
    <p class="motto">Child's Best Interests First. Integrity Over Narrative. Local Control. Always. Author Aziel Eliab.</p>
    <p class="lede">Local-first evidence integrity for pro se fathers in family court.</p>
    <a id="downloadBtn" class="btn block primary dl" href="/download?asset=${DEFAULT_ASSET}">Download</a>
    <p class="asset-note">${DEFAULT_ASSET} — ${n} counted. The Worker serves the gzip (HTTP 200) for every branch and fork.</p>
    <p class="banner">Local-first evidence integrity packaging. Not legal advice. Does not contact courts, Odyssey, email, or any cloud service. No telemetry. Author: Aziel Eliab.</p>
    <ul class="features">
      <li>Log, journal, and SHA-256 forensics on this computer.</li>
      <li>Verify, then import or export the receipt you hold.</li>
      <li>File templates, a guide, and the state you pick.</li>
    </ul>
  </header>
  <div class="card">
    <div class="nums">
      <p class="count">${v}<span>Views</span></p>
      <p class="count">${n}<span>Downloads</span></p>
    </div>
    <p class="kid">One-click install copies a Terminal command. After it finishes, run <code>forgereceipts ui</code>.</p>
    <button type="button" class="btn install" id="install-btn">One-click install</button>
    <pre id="install-cmd">curl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash</pre>
    <p class="kid">Then run: <code>forgereceipts ui</code> and open http://127.0.0.1:8787 (this computer only).</p>
    <p class="meta">The download count ticks on the Download click. No 302 to GitHub. Forks using this same link are counted automatically.</p>
    <p class="iso">Isolated counter: Worker <code>forgereceipts-download-tracker</code>, project <code>forgereceipts</code>, KV <code>FORGERECEIPTS_DOWNLOADS</code>. Not mixed with any other product. /v1 does not increment downloads.</p>
  </div>
  <div id="meshStrip" aria-label="Suite Live Nodes">
    <div class="live"><b id="meshLiveCount">0</b> Live Nodes</div>
    <div id="meshLine">Suite mesh: off (default). QNM-BUILD-1.0. QNS-CD-1.0. Not an anonymity network.</div>
    <div class="rollup">live <b id="qnmLive">0</b> · locked <b id="qnmLocked">0</b> · isolated <b id="qnmIsolated">0</b></div>
    <div>No Node Gate · No auto-heal · Aziel Eliab only</div>
    <div class="controls">
      <input id="meshBearer" type="text" maxlength="80" placeholder="bearer (required to enable)" aria-label="mesh bearer">
      <button id="meshEnable" type="button" title="Enable suite mesh. Declared bearer required. Default off.">Enable</button>
      <button id="meshDisable" type="button" title="Disable suite mesh (always allowed)">Disable</button>
      <button id="meshJoin" type="button" title="Join as forgereceipts. Refused while mesh is OFF. No auto-join.">Join</button>
      <button id="meshLeave" type="button" title="Leave this node. No auto-heal.">Leave</button>
    </div>
    <div id="meshProducts">Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · QNS-CD-1.0 photon QNS1 · not AnonBroadcast · not AZMail ring · not a Node Gate · no public qnsd proxy</div>
  </div>
    <script>
      (function () {
        var cmd = "curl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash";
        var btn = document.getElementById("install-btn");
        var pre = document.getElementById("install-cmd");
        if (!btn) return;
        btn.addEventListener("click", function () {
          function done(ok) {
            btn.textContent = ok ? "Copied! Paste in Terminal, then run forgereceipts ui" : "Select the command, copy it, then run forgereceipts ui";
            btn.classList.add("copied");
          }
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(cmd).then(function () { done(true); }).catch(function () { done(false); });
          } else {
            done(false);
            if (pre && window.getSelection) {
              var r = document.createRange();
              r.selectNodeContents(pre);
              var sel = window.getSelection();
              sel.removeAllRanges();
              sel.addRange(r);
            }
          }
        });
      })();
      (function () {
        function $(id) { return document.getElementById(id); }
        function meshNum() {
          for (var i = 0; i < arguments.length; i++) {
            var raw = arguments[i];
            if (raw == null || raw === "") continue;
            var n = typeof raw === "number" ? raw : Number(String(raw).replace(/,/g, ""));
            if (Number.isFinite(n) && n >= 0) return Math.floor(n);
          }
          return 0;
        }
        function unwrapMesh(j) {
          if (!j || typeof j !== "object") return {};
          if (j.result && typeof j.result === "object") return Object.assign({}, j, j.result);
          if (j.mesh && typeof j.mesh === "object") return Object.assign({}, j, j.mesh);
          return j;
        }
        function paintMesh(raw) {
          var j = unwrapMesh(raw);
          var on = j.enabled === true || j.enabled === 1 || String(j.status || "").toLowerCase() === "on";
          var r = (j.rollup && typeof j.rollup === "object") ? j.rollup : {};
          var live = on ? meshNum(r.live, j.live_nodes, j.live) : 0;
          var locked = on ? meshNum(r.locked, j.locked_nodes, j.locked) : 0;
          var isolated = on ? meshNum(r.isolated, j.isolated_nodes, j.isolated) : 0;
          $("meshLiveCount").textContent = String(live);
          $("qnmLive").textContent = String(live);
          $("qnmLocked").textContent = String(locked);
          $("qnmIsolated").textContent = String(isolated);
          var line = $("meshLine");
          if (on) line.textContent = "Suite mesh: on · live " + live + " · locked " + locked + " · isolated " + isolated + ". Not an anonymity network.";
          else if (j.status === "unavailable" || (j.ok === false && j.error)) line.textContent = "Suite mesh: off (unavailable). QNM-BUILD-1.0. QNS-CD-1.0. Not an anonymity network.";
          else line.textContent = "Suite mesh: off (default). QNM-BUILD-1.0. QNS-CD-1.0. Not an anonymity network.";
          var products = j.products_present || j.products || [];
          var names = Array.isArray(products) ? products.map(function (p) { return typeof p === "string" ? p : (p && (p.product || p.slug)) || ""; }).filter(Boolean) : [];
          var nodes = Array.isArray(j.nodes) ? j.nodes : [];
          var extra = names.length ? " · products " + names.join(", ") : (nodes.length ? " · " + nodes.length + " node labels" : "");
          var qns = (j.qns_cd && j.qns_cd.spec) ? String(j.qns_cd.spec) : "QNS-CD-1.0";
          $("meshProducts").textContent = "Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · " + qns + " photon QNS1 · not AnonBroadcast · not AZMail ring · not a Node Gate · no public qnsd proxy" + extra;
        }
        async function meshGet(path) {
          var r = await fetch(path, { headers: { "user-agent": "Mozilla/5.0", accept: "application/json" } });
          return r.json();
        }
        async function meshPost(path, payload) {
          var r = await fetch(path, { method: "POST", headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" }, body: JSON.stringify(payload || {}) });
          return r.json();
        }
        async function refreshMesh() {
          try {
            var status = await meshGet("/v1/mesh");
            var merged = status;
            var inner = unwrapMesh(status);
            var on = inner.enabled === true;
            if (on) {
              try {
                var nodes = await meshGet("/v1/mesh/nodes");
                merged = Object.assign({}, inner, unwrapMesh(nodes));
              } catch (e) { /* status is enough */ }
            }
            paintMesh(merged);
            var nodeId = sessionStorage.getItem("forgereceipts_mesh_node");
            if (on && nodeId) {
              try { await meshPost("/v1/mesh/heartbeat", { node_id: nodeId }); } catch (e) { /* no auto-heal */ }
            }
          } catch (e) {
            paintMesh({ ok: false, enabled: false, status: "unavailable", error: "mesh_unavailable" });
          }
        }
        $("meshEnable").onclick = async function () {
          var bearer = ($("meshBearer").value || "").trim();
          paintMesh(await meshPost("/v1/mesh/enable", bearer ? { bearer: bearer } : {}));
          refreshMesh();
        };
        $("meshDisable").onclick = async function () {
          sessionStorage.removeItem("forgereceipts_mesh_node");
          paintMesh(await meshPost("/v1/mesh/disable", {}));
          refreshMesh();
        };
        $("meshJoin").onclick = async function () {
          var j = await meshPost("/v1/mesh/join", { product: "forgereceipts", label: "ForgeReceipts Worker" });
          var inner = unwrapMesh(j);
          var id = inner.node_id || inner.id || (inner.session && inner.session.node_id);
          if (id) sessionStorage.setItem("forgereceipts_mesh_node", String(id));
          paintMesh(j);
          refreshMesh();
        };
        $("meshLeave").onclick = async function () {
          var id = sessionStorage.getItem("forgereceipts_mesh_node");
          if (id) await meshPost("/v1/mesh/leave", { node_id: id });
          sessionStorage.removeItem("forgereceipts_mesh_node");
          refreshMesh();
        };
        window.addEventListener("pagehide", function () {
          var id = sessionStorage.getItem("forgereceipts_mesh_node");
          if (!id || typeof navigator.sendBeacon !== "function") return;
          try { navigator.sendBeacon("/v1/mesh/leave", new Blob([JSON.stringify({ node_id: id })], { type: "application/json" })); } catch (e) { /* leave expires in 5 minutes */ }
        });
        refreshMesh();
        setInterval(refreshMesh, 30000);
        document.addEventListener("visibilitychange", function () { if (!document.hidden) refreshMesh(); });
      })();
    </script>
  <section class="card" aria-label="Per repo, branch, and fork">
    <h2>Per repo / branch / fork</h2>
    <ul>${breakdown}</ul>
  </section>

<section class="cite" id="cite">
  <h2>How to cite</h2>
  <p>Aziel Eliab. ForgeReceipts. https://github.com/AzielEliab/forgereceipts. https://forgereceipts-download-tracker.vibelock.workers.dev. https://doi.org/10.5281/zenodo.21436074.</p>
  <p><a href="https://aziel-runtime.vibelock.workers.dev/">Catalog</a> · <a href="https://github.com/AzielEliab/forgereceipts">GitHub</a> · <a href="https://forgereceipts-download-tracker.vibelock.workers.dev/download">Download</a> · <a href="https://forgereceipts-download-tracker.vibelock.workers.dev/cite.json">cite.json</a></p>
</section>
<footer class="quiet">
  <p>Apache-2.0 · Aziel Eliab · ForgeReceipts</p>
  <p><a href="${GITHUB_REPO}">GitHub</a> · <a href="${GITHUB_LATEST}">releases</a> · <a href="/openapi.json">OpenAPI</a> · <a href="/v1/skill">Skill</a> · <a href="/ai">AI runtime</a> · <a href="/stats">Stats</a> · <a href="/v1/mesh">Mesh</a> · <a href="https://doi.org/10.5281/zenodo.21436074">DOI</a></p>
  <p>Receipts stay on this computer. Forks are welcome and always allowed.</p>
</footer>
<!-- /gitbaby-seo -->
</body>
</html>`;
}


export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const mesh = await handleMesh(request, url, env);
    if (mesh) return mesh;

    const runtime = await handleRuntime(request, url, env);
    if (runtime) return runtime;

    if ((url.pathname === "/install.sh" || url.pathname === "/install.sh/") && request.method === "GET") {
      return new Response(installScript(), {
        status: 200,
        headers: {
          "Content-Type": "text/x-shellscript; charset=utf-8",
          "Cache-Control": "private, no-store",
          ...corsHeaders(),
        },
      });
    }


    if (url.pathname === "/" && request.method === "GET") {
      await incrementViews(env, request);
      return new Response(await indexHtml(env), {
        headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() },
      });
    }

    if (url.pathname === "/count" && request.method === "GET") {
      const stats = await collectStats(env, request);
      return json(shapeCountBody({
        project: PROJECT,
        views: stats.views || 0,
        downloads: stats.downloads || 0,
        total: stats.total || 0,
        views_human: stats.views_human,
        downloads_human: stats.downloads_human,
        botManagementAvailable: readBotManagement(request).available,
      }));
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      return json(await collectStats(env, request));
    }

    if (url.pathname === "/event" && request.method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "JSON body required" }, 400);
      }
      const dims = parseDims(body || {});
      const count = await increment(env, dims, request);
      return json({
        ok: true,
        key: kvKey(dims),
        count,
        owner: dims.owner,
        repo: dims.repo,
        branch: dims.branch,
        fork: dims.fork,
        asset: dims.asset || null,
      });
    }

    if (url.pathname === "/go" && (request.method === "GET" || request.method === "HEAD")) {
      const dims = parseDims(url.searchParams);
      const asset = dims.asset || DEFAULT_ASSET;
      dims.asset = asset;
      if (request.method === "GET") await increment(env, dims, request);
      return serveAsset(request, env, asset, { head: request.method === "HEAD" });
    }

    if ((url.pathname === "/download" || url.pathname.startsWith("/download/")) && (request.method === "GET" || request.method === "HEAD")) {
      const dims = parseDims(url.searchParams);
      if (!dims.asset && url.pathname.startsWith("/download/")) {
        dims.asset = decodeURIComponent(url.pathname.slice("/download/".length));
      }
      const asset = dims.asset || DEFAULT_ASSET;
      dims.asset = asset;
      if (request.method === "GET") await increment(env, dims, request);
      return serveAsset(request, env, asset, { head: request.method === "HEAD" });
    }


    // gitbaby-seo-routes
    if ((url.pathname === "/robots.txt" || url.pathname === "/robots.txt/") && request.method === "GET") {
      const body = "User-agent: *\nAllow: /\nSitemap: " + HOST + "/sitemap.xml\n";
      return new Response(body, {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8", ...corsHeaders() },
      });
    }
    if ((url.pathname === "/sitemap.xml" || url.pathname === "/sitemap.xml/") && request.method === "GET") {
      const locs = [HOST + "/", HOST + "/download", HOST + "/install.sh", HOST + "/v1/skill", HOST + "/v1/mesh", HOST + "/openapi.json", GITHUB_REPO];
      const xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + locs.map((u) => "  <url><loc>" + u + "</loc></url>").join("\n")
        + "\n</urlset>\n";
      return new Response(xml, {
        status: 200,
        headers: { "Content-Type": "application/xml; charset=utf-8", ...corsHeaders() },
      });
    }
    if ((url.pathname === "/cite.json" || url.pathname === "/cite.json/") && request.method === "GET") {
      return json({"author": "Aziel Eliab", "title": "ForgeReceipts", "github": "https://github.com/AzielEliab/forgereceipts", "download": "https://forgereceipts-download-tracker.vibelock.workers.dev/download", "doi": "10.5281/zenodo.21436074", "license": "Apache-2.0", "catalog": "https://aziel-runtime.vibelock.workers.dev/"});
    }
    // /gitbaby-seo-routes
    return json({ error: "not found" }, 404);
  },
};
