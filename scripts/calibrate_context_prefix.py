#!/usr/bin/env python3
"""Measure fresh context-only calls; this is not a task-accuracy experiment."""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, isolated, personal

SYSTEM = isolated.ROOT/'prompts/compact-context-system.txt'


class CompactContextBackend(isolated.ContainerBackend):
    def command(self, request, schema_path):
        command = super().command(request,schema_path)
        command[2:2] = ['--config','model_instructions_file='+json.dumps(str(SYSTEM))]
        return command


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    prompt = ('You are a context-only expert. Use only this question and context. '
        'Do not use tools or inspect files. Return action answer and put your answer in message. '
        'A controller calculated 17*19=323 and (323-17)/18=17. Check both results '
        'and give one arithmetic invariant for checking them. Do not claim any tool execution.')
    benchmark.write_new(args.output/'protocol.json',{
        'kind':'fresh_context_prefix_metering_and_mechanism_calibration_not_benchmark_accuracy',
        'model':'gpt-6.1-sol','reasoning_effort':'medium','prompt':prompt,
        'system_sha256':benchmark.digest(SYSTEM),'script_sha256':benchmark.digest(Path(__file__)),
        'schema':personal.EXPERT_SCHEMA,
        'official_config_reference':'https://learn.chatgpt.com/docs/config-file/config-reference',
        'frozen_study_prompts_unchanged':True})
    for label,backend in [('default',isolated.ContainerBackend()),('compact',CompactContextBackend())]:
        workspace=args.output.resolve()/('context-'+label);workspace.mkdir()
        request=personal.Request(label,'gpt-6.1-sol','expert',prompt,workspace,
                                 personal.EXPERT_SCHEMA,90,read_only=True,reasoning_effort='medium')
        response=backend.complete(request)
        benchmark.write_new(args.output/(label+'.json'),{
            'backend':backend.describe(),'response':asdict(response),
            'fresh_thread':True,'request':{'kind':'expert','read_only':True,'model':request.model}})
        print(json.dumps({'variant':label,'status':response.status,'usage':response.usage,
                          'answer':response.text,'tool_events':response.tool_events}),flush=True)
        if response.status!='completed' or any(type(response.usage.get(k)) is not int
                for k in ('input_tokens','cached_input_tokens','output_tokens')):
            raise RuntimeError('Calibration failed; preserve it without an implicit retry')
