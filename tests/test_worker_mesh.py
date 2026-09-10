"""Suite mesh Live Nodes + QNM-BUILD-1.0 contract + QNS-CD-1.0 cross-map.

Default OFF. live|locked|isolated. No Node Gate. No public qnsd proxy.
No auto-heal. Not anonymity.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MESH = (ROOT / "workers/download-tracker/src/mesh.js").read_text(encoding="utf-8")
RUNTIME = (ROOT / "workers/download-tracker/src/runtime.js").read_text(encoding="utf-8")
INDEX = (ROOT / "workers/download-tracker/src/index.js").read_text(encoding="utf-8")
WRANGLER = (ROOT / "workers/download-tracker/wrangler.toml").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKER_README = (ROOT / "workers/download-tracker/README.md").read_text(encoding="utf-8")


def test_mesh_contract_default_off_qnm_law() -> None:
    assert 'QNM_SPEC = "QNM-BUILD-1.0"' in MESH
    assert "MESH_DEFAULT_OFF = true" in MESH
    assert "MESH_ANONYMITY_NETWORK = false" in MESH
    assert "MESH_NODE_GATE = false" in MESH
    assert "MESH_AUTO_HEAL = false" in MESH
    assert "MESH_IDENTITY = IDENTITY" in MESH or '"Aziel Eliab"' in MESH
    assert 'MESH_PRODUCT = "forgereceipts"' in MESH
    assert 'MESH_PATH = "/v1/mesh"' in MESH
    assert "live|locked|isolated" in MESH
    assert "enabled_default: false" in MESH
    assert "anon_broadcast_publish_path: false" in MESH
    assert "Aziel Eliab" in MESH
    assert 'code: "MESH-OK"' in MESH
    assert "/v1/qnsd" not in MESH


def test_qns_cd_cross_map() -> None:
    assert 'QNS_CD_SPEC = "QNS-CD-1.0"' in MESH
    assert "export const QNS_CD" in MESH
    assert "photon QNS1 packet transfer" in MESH
    assert "https://github.com/AzielEliab/qnm-node" in MESH
    assert "https://github.com/AzielEliab/aziel-runtime" in MESH
    assert "https://github.com/AzielEliab/azinterface" in MESH
    assert "qnsd" in MESH
    assert "public_qnsd: false" in MESH
    assert "public_proxy: false" in MESH
    assert "softwares_tab: false" in MESH
    assert 'catalog_field: "qns_cd"' in MESH
    assert "export function attachQnsCd" in MESH
    assert "qns_cd_spec: QNS_CD_SPEC" in MESH
    assert "QNS-CD-1.0" in MESH  # MESH_NOTE
    assert "No public qnsd proxy" in MESH
    assert "QNS-CD-1.0" in README
    assert "QNS-CD-1.0" in SKILL
    assert "QNS-CD-1.0" in WORKER_README
    assert "photon QNS1" in INDEX
    assert "no public qnsd proxy" in INDEX


def test_mesh_pointer_and_openapi_helpers() -> None:
    assert "export function meshPointer" in MESH
    assert "export function meshOpenApiPaths" in MESH
    assert "export function parseMeshDoc" in MESH
    assert "export function emptyMesh" in MESH
    assert "export function alignLiveNodes" in MESH
    assert "export async function handleMesh" in MESH
    assert "fraggate_slug: MESH_SLUG" in MESH
    assert "forgereceipts_mesh_" in MESH


def test_index_routes_mesh_before_runtime_and_404() -> None:
    assert 'from "./mesh.js"' in INDEX
    assert "handleMesh(request, url, env)" in INDEX
    mesh_pos = INDEX.index("handleMesh(request, url, env)")
    runtime_pos = INDEX.index("handleRuntime(request, url, env)")
    not_found = INDEX.rindex('error: "not found"')
    assert mesh_pos < runtime_pos < not_found


def test_runtime_advertises_mesh_proxy_and_pointer() -> None:
    assert 'from "./mesh.js"' in RUNTIME
    assert "meshPointer" in RUNTIME
    assert "meshOpenApiPaths" in RUNTIME
    assert "...meshOpenApiPaths()" in RUNTIME
    assert "mesh: meshPointer()" in RUNTIME
    assert "/v1/mesh" in RUNTIME
    assert "QNM-BUILD-1.0" in RUNTIME
    assert "No Node Gate" in RUNTIME
    assert "No auto-heal" in RUNTIME
    assert 'path === "/v1/mesh"' in RUNTIME


def test_home_live_nodes_strip_no_node_gate() -> None:
    assert 'id="meshStrip"' in INDEX
    assert 'id="meshLiveCount"' in INDEX
    assert 'id="meshLine"' in INDEX
    assert "Live Nodes" in INDEX
    assert "QNM-BUILD-1.0" in INDEX
    assert "No Node Gate" in INDEX
    assert "No auto-heal" in INDEX
    assert "Not an anonymity network" in INDEX
    assert "/v1/mesh" in INDEX
    assert 'product: "forgereceipts"' in INDEX
    assert 'id="node-gate"' not in INDEX
    assert 'href="/node-gate"' not in INDEX
    assert "auto-heal this node" not in INDEX


def test_wrangler_binds_aziel_runtime_keeps_kv_id() -> None:
    assert "AZIEL_RUNTIME" in WRANGLER
    assert 'service = "aziel-runtime"' in WRANGLER
    assert 'id = "a40597120bcf4e1d9b26d0c4a1b2f05d"' in WRANGLER
    assert "/v1/mesh" in WRANGLER or "/v1/*" in WRANGLER


def test_docs_advertise_mesh_proxy() -> None:
    assert "/v1/mesh" in README
    assert "/v1/mesh" in SKILL
    assert "QNM-BUILD-1.0" in WORKER_README
    assert "AZIEL_RUNTIME" in WORKER_README
    assert "Live Nodes" in WORKER_README
    assert "Aziel Eliab" in MESH
    assert "Not legal advice" in MESH
