import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SERVER = os.path.join(ROOT, "server.py")
PYTHON = sys.executable

class McpE2ETest(unittest.TestCase):
    def call(self, messages, timeout=60):
        payload = "".join(json.dumps(m) + "\n" for m in messages)
        p = subprocess.run([PYTHON, SERVER], input=payload, text=True,
                           capture_output=True, cwd=ROOT, timeout=timeout)
        self.assertEqual(p.returncode, 0, p.stderr)
        return [json.loads(line) for line in p.stdout.splitlines() if line.strip()]

    def test_initialize_and_tools_list_are_generic(self):
        out = self.call([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ])
        names = {x["name"] for x in out[1]["result"]["tools"]}
        self.assertEqual(names, {"search_listings", "get_listing", "check_availability", "calculate_route"})

    def test_search_tool_returns_compact_distance_listings(self):
        out = self.call([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "search_listings", "arguments": {"query": "product", "location": "Berlin", "radius_km": 30, "max_price": 1800, "limit": 3, "compact": True, "include_distance": True, "origin_latitude": 52.52, "origin_longitude": 13.405}}}])
        result = out[0]["result"]["structuredContent"]
        self.assertIn("listings", result)
        self.assertLessEqual(len(result["listings"]), 3)
        if result["listings"]:
            self.assertIn("latitude", result["listings"][0])
            self.assertIn("longitude", result["listings"][0])

if __name__ == "__main__":
    unittest.main()
