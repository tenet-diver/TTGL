#!/usr/bin/env python3
"""Modern SDK catalog/error boundaries only; no image, container or model run."""
import hashlib,json,secrets,subprocess,sys
from pathlib import Path
from mcp_memory_probe import Client
ROOT=Path(__file__).resolve().parents[3];GLOBAL=ROOT/'work/security/context-memory-20261107'
def main():
    out=GLOBAL/'native-worker-v2-probe-001';out.mkdir();review=GLOBAL/'mcp-memory-review';source=Path(__file__).with_name('native_worker_v2.mjs');entry=review/'native-worker-v2.mjs'
    if source.read_bytes()!=entry.read_bytes():raise ValueError('Runtime source differs')
    receipt=json.loads((review/'pre-install-receipt.json').read_text())
    if receipt['known_findings']:raise ValueError('Known findings block')
    owned='ttgl-worker-'+secrets.token_hex(12)
    inspected=subprocess.run(['docker','container','inspect',owned],capture_output=True)
    if inspected.returncode==0:raise ValueError('Expected absent owned identity')
    wrapper=review/'native-worker-v2-probe-entry.mjs';wrapper.write_text('process.argv[2]='+json.dumps(owned)+';process.argv[3]="/testbed";await import("./native-worker-v2.mjs");\n')
    client=Client(wrapper,out/'unused.jsonl',out/'server-stderr.log')
    try:
        client.request('initialize',dict(protocolVersion='2025-06-18',capabilities={},clientInfo=dict(name='ttgl-boundary-probe',version='1')));client.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');client.p.stdin.flush();tools=client.request('tools/list',{})['tools'];reply=client.request('tools/call',dict(name='shell',arguments=dict(command='printf TTGL_SHOULD_NOT_RUN',timeout_seconds=1)));passed=[t['name'] for t in tools]==['shell'] and reply.get('isError') is True
    finally:client.close()
    invalid=subprocess.run(['node',str(entry),'invalid;injection','/testbed'],capture_output=True,text=True,timeout=10);checks=dict(one_bounded_tool_catalog=passed,invalid_identity_rejected=invalid.returncode!=0 and 'owned worker container name is required' in invalid.stderr)
    (out/'result.json').write_text(json.dumps(dict(checks=checks,passed=all(checks.values()),model_calls=0,containers_created=0,images_executed=0,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Maintained modern SDK stdio catalog and absent-container/error/name boundaries; not a real actor isolation gate or benchmark result.'),indent=2)+'\n');print(json.dumps(checks));assert all(checks.values())
if __name__=='__main__':main()
