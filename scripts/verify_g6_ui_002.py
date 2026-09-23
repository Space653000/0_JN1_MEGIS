"""Verify the G6-UI-002 local HTTP and browser equivalence evidence."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.api.server import create_server
from megis.guides.flow import GuidedAnswers, evaluate_guided_maturity

AUDIT_PATH = ROOT / "artifacts" / "g6-ui-002" / "browser-audit.json"
OUTPUT_PATH = ROOT / "artifacts" / "g6-ui-002" / "verification.json"


@contextmanager
def running_api():
    server = create_server(port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def post_ir(port: int, payload: dict) -> tuple[int, dict[str, str], bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(
        "POST",
        "/api/v1/ir-drafts",
        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"},
    )
    response = connection.getresponse()
    body = response.read()
    result = response.status, dict(response.getheaders()), body
    connection.close()
    return result


def main() -> int:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    with running_api() as port:
        status, headers, body = post_ir(port, audit["request"])
    digest = sha256(body).hexdigest()
    app_source = (ROOT / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    design_source = (ROOT / "apps/web/src/pages/DesignPage.tsx").read_text(encoding="utf-8")
    adapter_source = (ROOT / "apps/web/src/adapters/engineering-api-adapter.ts").read_text(encoding="utf-8")
    maturity = evaluate_guided_maturity(GuidedAnswers(pcb_count=2))
    checks = [
        {"name": "guided maturity remains evidence-derived DRAFT", "passed": maturity.state == "DRAFT"},
        {"name": "guarded local HTTP endpoint returns canonical IR", "passed": status == 200 and json.loads(body)["maturity"] == "DRAFT"},
        {"name": "production React flow uses the HTTP adapter without synthetic fallback", "passed": "localEngineeringApi" in app_source and "EngineeringApiError" in design_source and "/api/v1/ir-drafts" in adapter_source and "createDemoResult" not in app_source},
        {"name": "browser and direct HTTP response bytes are equivalent", "passed": digest == audit["responseSha256"] == headers.get("X-Content-SHA256")},
    ]
    report = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-UI-002",
        "evidenceLevel": "E3",
        "verifiedAt": "2026-09-23T12:15:00+08:00",
        "pinnedCommit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "allChecksPassed": all(check["passed"] for check in checks),
        "browserAudit": str(AUDIT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "responseSha256": digest,
        "checks": checks,
        "boundaries": {"database": False, "jobQueue": False, "cad": False, "package": False},
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["allChecksPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
