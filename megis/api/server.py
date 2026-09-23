"""Guarded, synchronous, local-only HTTP seam for G6-UI-002."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from typing import Any
from uuid import uuid4

from megis.errors import MegisError
from megis.guides.capabilities import build_manifest
from megis.guides.flow import build_ir_via_api
from megis.guides.questions import guided_questions

API_HOST = "127.0.0.1"
API_PORT = 4174
ALLOWED_ORIGIN = "http://127.0.0.1:4173"
MAX_BODY_BYTES = 65_536
SOCKET_TIMEOUT_SECONDS = 5
_CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class ApiConfigurationError(ValueError):
    """Raised when the server would escape the approved loopback boundary."""


class MegisApiServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _canonical_json(document: Any) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


class MegisApiHandler(BaseHTTPRequestHandler):
    """Serve the versioned IR-draft contract without persistence or jobs."""

    server_version = "MEGISLocalIR/1.0"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(SOCKET_TIMEOUT_SECONDS)

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _correlation_id(self) -> str:
        supplied = self.headers.get("X-Correlation-ID", "")
        if _CORRELATION_PATTERN.fullmatch(supplied):
            return supplied
        return f"g6ui2-{uuid4().hex}"

    def _origin(self) -> str | None:
        return self.headers.get("Origin")

    def _guard_request(self, correlation_id: str) -> bool:
        host = self.headers.get("Host", "")
        origin = self._origin()
        if not re.fullmatch(r"127\.0\.0\.1(?::\d+)?", host):
            self._write_error(403, "MEGIS-SYS-002", correlation_id, "untrusted Host header")
            return False
        if origin not in (None, ALLOWED_ORIGIN):
            self._write_error(403, "MEGIS-SYS-002", correlation_id, "untrusted Origin header")
            return False
        return True

    def _headers(self, status: int, content_type: str, length: int, correlation_id: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Correlation-ID", correlation_id)
        if self._origin() == ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
            self.send_header("Vary", "Origin")
        self.end_headers()

    def _write_json(self, status: int, document: Any, correlation_id: str) -> None:
        payload = _canonical_json(document)
        self._headers(status, "application/json; charset=utf-8", len(payload), correlation_id)
        self.wfile.write(payload)

    def _write_ir(self, payload: bytes, correlation_id: str) -> None:
        self._headers(200, "application/json; charset=utf-8", len(payload), correlation_id)
        self.wfile.write(payload)

    def _write_error(
        self,
        status: int,
        code: str,
        correlation_id: str,
        detail: Any,
        *,
        entity_refs: tuple[str, ...] = (),
    ) -> None:
        error = MegisError(
            code,
            engineer_detail=detail,
            entity_refs=entity_refs,
            correlation_id=correlation_id,
        )
        self._write_json(status, {"error": error.error_object.to_dict()}, correlation_id)

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        correlation_id = self._correlation_id()
        if not self._guard_request(correlation_id):
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Correlation-ID")
        self.send_header("X-Correlation-ID", correlation_id)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        correlation_id = self._correlation_id()
        if not self._guard_request(correlation_id):
            return
        routes: dict[str, Any] = {
            "/api/v1/health": {
                "schemaVersion": "1.0.0",
                "service": "megis-local-ir-api",
                "status": "ready",
            },
            "/api/v1/capabilities": build_manifest,
            "/api/v1/questions": lambda: {
                "schemaVersion": "1.0.0",
                "questions": list(guided_questions()),
            },
        }
        provider = routes.get(self.path)
        if provider is None:
            self._write_error(404, "MEGIS-SYS-002", correlation_id, "unknown API route")
            return
        document = provider() if callable(provider) else provider
        self._write_json(200, document, correlation_id)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        correlation_id = self._correlation_id()
        if not self._guard_request(correlation_id):
            return
        if self.path != "/api/v1/ir-drafts":
            self._write_error(404, "MEGIS-SYS-002", correlation_id, "unknown API route")
            return
        if self.headers.get_content_type() != "application/json":
            self._write_error(415, "MEGIS-SCH-001", correlation_id, "Content-Type must be application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0:
            self._write_error(411, "MEGIS-SCH-001", correlation_id, "Content-Length is required")
            return
        if length > MAX_BODY_BYTES:
            self._write_error(413, "MEGIS-SCH-001", correlation_id, "request body exceeds 65536 bytes")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            ir = build_ir_via_api(payload).encode("utf-8")
        except MegisError as exc:
            self._write_error(
                422,
                exc.error_object.code,
                correlation_id,
                exc.error_object.engineer_detail,
                entity_refs=exc.error_object.entity_refs,
            )
            return
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            self._write_error(400, "MEGIS-SCH-001", correlation_id, str(exc))
            return
        self._write_ir(ir, correlation_id)


def create_server(*, host: str = API_HOST, port: int = API_PORT) -> MegisApiServer:
    """Create a loopback-only server; callers control its lifecycle."""

    if host != API_HOST:
        raise ApiConfigurationError("MEGIS local API must bind exactly to 127.0.0.1")
    if not isinstance(port, int) or not 0 <= port <= 65_535:
        raise ApiConfigurationError("port must be an integer from 0 through 65535")
    return MegisApiServer((host, port), MegisApiHandler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=API_HOST)
    parser.add_argument("--port", type=int, default=API_PORT)
    args = parser.parse_args()
    try:
        server = create_server(host=args.host, port=args.port)
    except ApiConfigurationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ready", "host": args.host, "port": args.port}, ensure_ascii=False), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
