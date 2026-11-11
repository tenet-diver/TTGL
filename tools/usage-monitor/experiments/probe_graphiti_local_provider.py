#!/usr/bin/env python3
"""Actual stock Graphiti client/local-provider compatibility, not memory efficacy.

Run with the reviewed graphiti-runtime on PYTHONPATH. The SDK HTTP hooks retain
every request/response and prevent automatic retries from invoking the model.
Model selection diagnostics remain separate from scored coding assignments.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


async def probe(root, cases_file, model, mode):
    from pydantic import BaseModel
    from openai import AsyncOpenAI, DefaultAsyncHttpxClient
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.prompts.models import Message

    class Fact(BaseModel):
        project: str
        test_command: str | None
        verified: bool

    cases = json.loads(cases_file.read_text())
    state = {'case': None, 'sent': 0}
    observations = []

    def record(row):
        observations.append(row)
        with (root / 'http-events.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')

    async def before(request):
        if state['sent'] >= 1:
            record(dict(case=state['case'], event='blocked_automatic_retry'))
            raise RuntimeError('One provider invocation per diagnostic case')
        state['sent'] += 1
        record(dict(case=state['case'], event='request', at=datetime.now(timezone.utc).isoformat(),
                    url=str(request.url), body=json.loads(request.content)))

    async def after(response):
        await response.aread()
        record(dict(case=state['case'], event='response', at=datetime.now(timezone.utc).isoformat(),
                    status=response.status_code, body=response.json()))

    root.mkdir(exist_ok=False)
    (root / 'cases.json').write_bytes(cases_file.read_bytes())
    with (root / 'started.json').open('x') as stream:
        json.dump(dict(at=datetime.now(timezone.utc).isoformat(), model=model,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            cases_sha256=hashlib.sha256(cases_file.read_bytes()).hexdigest(),
            kind='local_provider_development_diagnostic', max_tokens=128,
            timeout_seconds=120, sdk_max_retries=0,
            stock_graphiti_retry='HTTP hook blocks additional inference',
            mode=mode, provider_constraint_support='Must be checked from provider receipts'), stream, indent=2)
    results = []
    async with DefaultAsyncHttpxClient(event_hooks={'request': [before], 'response': [after]}, timeout=120) as transport:
        sdk = AsyncOpenAI(api_key='local-only', base_url='http://127.0.0.1:8450/v1',
                          max_retries=0, http_client=transport)
        llm = OpenAIGenericClient(config=LLMConfig(api_key='local-only',
            base_url='http://127.0.0.1:8450/v1', model=model, small_model=model,
            temperature=0, max_tokens=128), client=sdk, max_tokens=128, structured_output_mode=mode)
        for name, text, expected in cases:
            state.update(case=name, sent=0)
            start = time.perf_counter()
            try:
                output = await asyncio.wait_for(llm.generate_response([
                    Message(role='system', content='Extract only the latest evidence-backed procedure. Set verified true only if a command was executed and passed. Otherwise set verified false and test_command null. Do not assume a command from prior knowledge.'),
                    Message(role='user', content=text)], response_model=Fact, max_tokens=128), timeout=120)
                parsed = Fact.model_validate(output).model_dump()
                result = dict(case=name, result=parsed, expected=expected, passed=parsed == expected,
                              seconds=time.perf_counter() - start)
            except Exception as error:
                results.append(dict(case=name, error=repr(error), passed=False,
                    seconds=time.perf_counter() - start, further_cases_stopped=True))
                break
            results.append(result)
            print(json.dumps(result), flush=True)
    requests = [r for r in observations if r['event'] == 'request']
    responses = [r for r in observations if r['event'] == 'response']
    usage = [r['body'].get('usage') for r in responses]
    complete = bool(requests) and len(requests) == len(responses) and all(u is not None for u in usage)
    result = dict(at=datetime.now(timezone.utc).isoformat(), model=model, cases=results,
        passed=len(results) == len(cases) and all(r['passed'] for r in results),
        actual_http_requests=len(requests), responses_observed=len(responses),
        blocked_retries=sum(r['event'] == 'blocked_automatic_retry' for r in observations),
        observed_usage_complete=complete, usage=usage,
        observed_usage_total={k: sum(u.get(k, 0) for u in usage) for k in ['prompt_tokens', 'completion_tokens', 'total_tokens']} if complete else None,
        limit='Synthetic Graphiti client checks only; graph ingestion, MCP, cross-agent retrieval and coding performance not established.')
    with (root / 'result.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--mode', choices=['json_object', 'json_schema'], default='json_object')
    args = parser.parse_args()
    asyncio.run(probe(args.root, args.cases, args.model, args.mode))
