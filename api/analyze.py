"""
Vercel serverless function: POST /api/analyze with { "url": "https://..." }
Runs BrandAnalyzer and returns the analysis JSON (no file write; stateless).
"""
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure project root is on path (Vercel CWD is project root, but sys.path may not include it)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from gpt_web_descrirption import BrandAnalyzer


def _send_json(self, status: int, body: dict):
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            _send_json(self, 400, {"success": False, "error": "Body required"})
            return

        try:
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            _send_json(self, 400, {"success": False, "error": "Invalid JSON"})
            return

        url = (data.get("url") or "").strip()
        if not url:
            _send_json(self, 400, {"success": False, "error": "URL is required"})
            return
        if not url.startswith(("http://", "https://")):
            _send_json(self, 400, {"success": False, "error": "URL must start with http:// or https://"})
            return

        try:
            analyzer = BrandAnalyzer()
            result = analyzer.analyze(url)
            _send_json(self, 200, {"success": True, "data": result, "redirect": "/moodboard.html"})
        except ValueError as e:
            _send_json(self, 400, {"success": False, "error": str(e)})
        except Exception as e:
            _send_json(self, 500, {"success": False, "error": str(e)})
