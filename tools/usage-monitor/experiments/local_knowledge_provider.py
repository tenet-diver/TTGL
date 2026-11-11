#!/usr/bin/env python3
"""Small local OpenAI chat adapter over maintained Transformers and LMFE.

Missing transport behavior only: schema-constrained decoding and immutable
per-request evidence. This is an adapted provider, not a stock inference server
or a new knowledge system. No backend memory/extraction code is implemented.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
import uuid


class Engine:
    def __init__(self, model_path, alias, evidence, compatibility_aliases=(), dtype='bfloat16', generation_seconds=90, dynamic_int8=False):
        if os.environ.get('HF_HUB_OFFLINE') != '1':
            raise ValueError('Offline model loading required')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        self.torch = torch
        self.dtype, self.generation_seconds = dtype, generation_seconds
        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        self.alias, self.evidence = alias, evidence
        self.aliases = {alias, *compatibility_aliases}
        self.lock = threading.Lock()
        started = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
            trust_remote_code=False, dtype=getattr(torch,dtype), device_map='cpu').eval()
        if dynamic_int8:
            if dtype != 'float32':
                raise ValueError('Dynamic INT8 profile requires float32 source weights')
            self.model = torch.ao.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
        self.tokenizer_data = build_token_enforcer_tokenizer_data(self.tokenizer)
        with (evidence / 'ready.json').open('x') as stream:
            json.dump(dict(at=datetime.now(timezone.utc).isoformat(), alias=alias,
                model_path=str(model_path), accepted_aliases=sorted(self.aliases), load_seconds=time.perf_counter() - started,
                dtype=dtype, dynamic_int8=dynamic_int8,
                quantization='PyTorch legacy dynamic qint8 Linear API; deprecated in favor of separately packaged torchao' if dynamic_int8 else None,
                generation_wall_limit_seconds=generation_seconds, cpu_threads=2, request_concurrency=1,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                claim='Provider readiness only; zero warmup/generation requests'), stream, indent=2)

    def validate(self, body):
        if not isinstance(body, dict) or body.get('model') not in self.aliases:
            raise ValueError('Use the configured model alias')
        if body.get('stream') or body.get('tools') or body.get('tool_choice'):
            raise ValueError('This provider supports non-streaming text/JSON chat only')
        limit = body.get('max_tokens', 512)
        if type(limit) is not int or not 1 <= limit <= 16384:
            raise ValueError('max_tokens must be between1 and16384')
        messages = body.get('messages')
        if not isinstance(messages, list) or not messages or any(
            not isinstance(m, dict) or m.get('role') not in ('system', 'user', 'assistant')
            or not isinstance(m.get('content'), str) for m in messages):
            raise ValueError('Text messages required')
        fmt = body.get('response_format') or {'type': 'text'}
        if not isinstance(fmt, dict) or fmt.get('type') not in ('text', 'json_object', 'json_schema'):
            raise ValueError('Text, JSON object or JSON schema response format required')
        description = fmt.get('json_schema', {})
        if not isinstance(description, dict):
            raise ValueError('JSON schema description object required')
        schema = description.get('schema') if fmt['type'] == 'json_schema' else ({} if fmt['type'] == 'json_object' else None)
        if fmt['type'] != 'text' and not isinstance(schema, dict):
            raise ValueError('JSON schema object required')
        if type(body.get('logprobs', False)) is not bool:
            raise ValueError('logprobs must be boolean')
        top = body.get('top_logprobs', 0)
        if type(top) is not int or not 0 <= top <= 20:
            raise ValueError('top_logprobs must be between0 and20')
        bias = body.get('logit_bias') or {}
        if not isinstance(bias, dict) or any(not str(k).isdigit() or not 0 <= int(k) < self.model.config.vocab_size or type(v) not in (int, float) or not -100 <= v <= 100 for k, v in bias.items()):
            raise ValueError('Invalid local tokenizer logit_bias')
        temperature = body.get('temperature', 0)
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
            raise ValueError('Invalid temperature')
        return messages, schema, limit, temperature

    def generate(self, body):
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
        messages, schema, limit, temperature = self.validate(body)
        ident = uuid.uuid4().hex
        received = time.perf_counter()
        with (self.evidence / (ident + '.started.json')).open('x') as stream:
            json.dump(dict(id=ident, at=datetime.now(timezone.utc).isoformat(), request=body,
                automatic_retries=0, source='local provider; credentials/headers not retained'), stream)
        try:
            with self.lock:
                began = time.perf_counter()
                cpu_start = time.process_time()
                chat = messages
                if schema is not None:
                    instruction = ('Return one JSON DATA INSTANCE conforming to the schema. '
                        'Return data, never the schema itself. JSON schema: ' + json.dumps(schema))
                    chat = [dict(role='system', content=instruction), *messages]
                text = self.tokenizer.apply_chat_template(chat, tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
                inputs = self.tokenizer(text, return_tensors='pt')
                prompt_tokens = int(inputs['input_ids'].shape[1])
                if prompt_tokens > 8192:
                    raise ValueError('Input exceeds8192 tokens')
                seed = body.get('seed', 41)
                if type(seed) is not int:
                    raise ValueError('Integer seed required')
                self.torch.manual_seed(seed)
                options = dict(max_new_tokens=limit, max_time=self.generation_seconds, do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id, eos_token_id=self.tokenizer.eos_token_id)
                if schema is not None:
                    options['prefix_allowed_tokens_fn'] = build_transformers_prefix_allowed_tokens_fn(self.tokenizer_data, JsonSchemaParser(schema))
                if body.get('logit_bias'):
                    from transformers import LogitsProcessor, LogitsProcessorList
                    bias = {int(k): v for k, v in body['logit_bias'].items()}
                    class Bias(LogitsProcessor):
                        def __call__(self, input_ids, scores):
                            for token, value in bias.items():
                                scores[:, token] += value
                            return scores
                    options['logits_processor'] = LogitsProcessorList([Bias()])
                if body.get('logprobs'):
                    options.update(return_dict_in_generate=True, output_scores=True)
                if temperature > 0:
                    options['temperature'] = temperature
                with self.torch.inference_mode():
                    generated = self.model.generate(**inputs, **options)
                output = (generated.sequences[0] if body.get('logprobs') else generated[0])[prompt_tokens:]
                content = self.tokenizer.decode(output, skip_special_tokens=True)
                finished = time.perf_counter()
                completion_tokens = int(output.shape[0])
                stopped = bool(completion_tokens and int(output[-1]) == self.tokenizer.eos_token_id)
                response = dict(id='chatcmpl-' + ident, object='chat.completion', created=int(time.time()),
                    model=self.alias, choices=[dict(index=0, finish_reason='stop' if stopped else 'length',
                    message=dict(role='assistant', content=content))],
                    usage=dict(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                               total_tokens=prompt_tokens + completion_tokens))
                if body.get('logprobs'):
                    probabilities = []
                    def token_record(token, probability):
                        token_text = self.tokenizer.decode([token], skip_special_tokens=False)
                        return dict(token=token_text, logprob=float(probability), bytes=list(token_text.encode()))
                    for token, scores in zip(output.tolist(), generated.scores, strict=True):
                        logs = scores[0].float().log_softmax(-1)
                        entry = token_record(token, logs[token])
                        values, indices = logs.topk(body.get('top_logprobs', 0))
                        entry['top_logprobs'] = [token_record(t, p) for t, p in zip(indices.tolist(), values.tolist())]
                        probabilities.append(entry)
                    response['choices'][0]['logprobs'] = dict(content=probabilities)
                record = dict(id=ident, at=datetime.now(timezone.utc).isoformat(), response=response,
                    queue_seconds=began - received, operation_seconds=finished - began,
                    process_cpu_seconds=time.process_time() - cpu_start, seed=seed,
                    request_temperature=temperature, new_request_kv_cache=True,
                    requested_model=body['model'], actual_model_alias=self.alias,
                    generation_wall_limit_seconds=self.generation_seconds,
                    logit_bias_semantics='Numeric IDs refer to the served Qwen tokenizer; no GPT tokenizer translation',
                    counter_definition='actual encoded input IDs and newly generated IDs, including EOS when generated')
                with (self.evidence / (ident + '.completed.json')).open('x') as stream:
                    json.dump(record, stream)
                return response
        except BaseException as error:
            with (self.evidence / (ident + '.failed.json')).open('x') as stream:
                json.dump(dict(id=ident, error=repr(error), elapsed_seconds=time.perf_counter() - received,
                    usage=None, at=datetime.now(timezone.utc).isoformat(), automatic_retries=0), stream)
            raise


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self.reply(200, dict(ready=True, model=self.server.engine.alias))
        if self.path == '/v1/models':
            return self.reply(200, dict(object='list', data=[dict(id=self.server.engine.alias,
                object='model', created=0, owned_by='local-experiment')]))
        self.reply(404, dict(error='Unsupported route'))

    def do_POST(self):
        if self.path != '/v1/chat/completions':
            return self.reply(404, dict(error='Unsupported route'))
        body = None
        try:
            self.connection.settimeout(10)
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024 * 1024:
                raise ValueError('Invalid request size')
            body = json.loads(self.rfile.read(length))
            self.server.engine.validate(body)
        except (ValueError, TypeError, OSError) as error:
            ident = uuid.uuid4().hex
            with (self.server.engine.evidence / (ident + '.rejected.json')).open('x') as stream:
                json.dump(dict(id=ident, at=datetime.now(timezone.utc).isoformat(),
                    request=body, reason=str(error), model_invocations=0,
                    source='HTTP contract rejected before Engine.generate'), stream)
            return self.reply(400, dict(error=dict(message=str(error), type='invalid_request_error')))
        try:
            result = self.server.engine.generate(body)
        except Exception as error:
            return self.reply(422, dict(error=dict(message=type(error).__name__, type='local_generation_error')))
        self.reply(200, result)

    def log_message(self, *_args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--alias', default='local-knowledge')
    parser.add_argument('--compatibility-alias', action='append', default=[])
    parser.add_argument('--dtype', choices=['float32','bfloat16'], default='bfloat16')
    parser.add_argument('--dynamic-int8', action='store_true')
    parser.add_argument('--generation-seconds', type=int, default=90)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8450)
    args = parser.parse_args()
    os.umask(0o077)
    args.evidence.mkdir(parents=True, exist_ok=False)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    if not 1<=args.generation_seconds<=600:
        raise ValueError('generation-seconds must be between1 and600')
    server.engine = Engine(args.model_path, args.alias, args.evidence, args.compatibility_alias,args.dtype,args.generation_seconds,args.dynamic_int8)
    print('Local constrained provider ready; no inference retries.', flush=True)
    server.serve_forever()
