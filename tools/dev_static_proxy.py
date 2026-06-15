#!/usr/bin/env python3
from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import urllib.error
import urllib.request


class ProxyHandler(SimpleHTTPRequestHandler):
    backend_url = "http://127.0.0.1:18080"

    def do_GET(self) -> None:
        if self.path.startswith("/api/views"):
            self._proxy()
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/views"):
            self._proxy()
            return
        self.send_error(404, "Not found")

    def _proxy(self) -> None:
        body = None
        length = self.headers.get("Content-Length")
        if length:
            body = self.rfile.read(int(length))

        request = urllib.request.Request(
            self.backend_url + self.path,
            data=body,
            method=self.command,
            headers={
                "Content-Type": self.headers.get("Content-Type", "application/json"),
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as error:
            payload = error.read()
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except OSError as error:
            payload = f'{{"error":"proxy error: {error}"}}\n'.encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Hugo output and proxy /api/views to the local backend.")
    parser.add_argument("--root", required=True, help="Static Hugo output directory.")
    parser.add_argument("--backend", default="http://127.0.0.1:18080", help="Backend base URL.")
    parser.add_argument("--host", default="127.0.0.1", help="Listen host.")
    parser.add_argument("--port", default=1313, type=int, help="Listen port.")
    args = parser.parse_args()

    handler = lambda *handler_args, **handler_kwargs: ProxyHandler(
        *handler_args,
        directory=args.root,
        **handler_kwargs,
    )
    ProxyHandler.backend_url = args.backend.rstrip("/")

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"serving {args.root} on http://{args.host}:{args.port}, proxying /api/views to {ProxyHandler.backend_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
