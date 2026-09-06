#!/home/christian/.hermes/venvs/kleinanzeigen/bin/python
"""Kleinanzeigen bike search/ranking used by the cron job and MCP."""
import importlib.util

PATH = "/home/christian/.hermes/scripts/kleinanzeigen-bike-search.py"
spec = importlib.util.spec_from_file_location("bike_search_impl", PATH)
_impl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_impl)

def run():
    return _impl.run_search()
