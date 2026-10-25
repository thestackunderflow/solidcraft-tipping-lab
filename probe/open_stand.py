import json, sys
sys.path.insert(0, '/t')
from mcp_client import McpClient
def call(m, n, a):
    r = m.call_tool(n, a); t = '\n'.join(b['text'] for b in r.get('content', []) if b.get('type') == 'text')
    try: return json.loads(t)
    except Exception: return t
m = McpClient(["solidcraft-cli", "mcp", "--allow-path", "/t"]); m.start()
print(str(call(m, 'open', {'path': '/t/stand.solidcraft'}))[:800])
print(json.dumps(call(m, 'measure', {}))[:900])
print(json.dumps(call(m, 'execute', {'command': 'parameters.list', 'params': {}}))[:1500])
print(json.dumps(call(m, 'inspect_design', {}))[:2500])
m.close()
