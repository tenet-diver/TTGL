#!/usr/bin/env python3
import json,urllib.request
with urllib.request.urlopen('http://127.0.0.1:8766/api/agent-context',timeout=15) as response:
 print(json.dumps(json.load(response),indent=2))
