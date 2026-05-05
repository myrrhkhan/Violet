#!/usr/bin/env python3
import argparse
import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def build_rie_url(rie_port: int) -> str:
    return f"http://127.0.0.1:{rie_port}/2015-03-31/functions/function/invocations"


class ProxyHandler(BaseHTTPRequestHandler):
    rie_url = ""

    def _set_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/predict-ocr":
            self.send_response(404)
            self._set_cors()
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        event = {
            "httpMethod": "POST",
            "isBase64Encoded": True,
            "body": base64.b64encode(body).decode("utf-8"),
        }
        payload = json.dumps(event).encode("utf-8")

        try:
            req = Request(
                self.rie_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=600) as resp:
                response_body = resp.read().decode("utf-8")
            parsed = json.loads(response_body)
            status_code = int(parsed.get("statusCode", 200))
            lambda_body = parsed.get("body", "")
            if isinstance(lambda_body, str):
                output = lambda_body.encode("utf-8")
            else:
                output = json.dumps(lambda_body).encode("utf-8")

            self.send_response(status_code)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(output)
        except HTTPError as exc:
            self.send_response(502)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
        except Exception as exc:
            self.send_response(500)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Proxy /predict-ocr to local Lambda RIE")
    parser.add_argument("--port", type=int, default=3001, help="Local proxy listen port")
    parser.add_argument("--rie-port", type=int, default=9000, help="Lambda RIE port")
    args = parser.parse_args()

    ProxyHandler.rie_url = build_rie_url(args.rie_port)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"Proxy listening on http://127.0.0.1:{args.port}/predict-ocr")
    print(f"Forwarding to {ProxyHandler.rie_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
