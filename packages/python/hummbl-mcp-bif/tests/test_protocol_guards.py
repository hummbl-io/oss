"""Protocol guard tests: non-dict JSON-RPC payloads must not kill the loop."""

import io
import json

import bif_mcp_server as srv


def test_non_dict_payloads_get_invalid_request(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO('123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "tools/list"}\n'),
    )
    srv.main()
    out = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    errors = [m for m in out if "error" in m]
    assert len(errors) == 2
    assert all(e["error"]["code"] == -32600 for e in errors)
    assert any(m.get("id") == 7 for m in out)
