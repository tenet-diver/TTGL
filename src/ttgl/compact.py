"""Compact context-only expert instructions, preserving acting-agent settings."""
import json
from pathlib import Path

from . import benchmark, isolated
from .policy import PolicyBackend

SYSTEM = isolated.ROOT/'prompts/compact-context-system.txt'
DRIVER = isolated.ROOT/'scripts/run_compact_policy_study.py'


class CompactPolicyBackend(PolicyBackend):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.frozen_compact = self.compact_identity()

    def compact_identity(self):
        return {'system_sha256':benchmark.digest(SYSTEM),
                'source_sha256':benchmark.digest(Path(__file__)),
                'driver_sha256':benchmark.digest(DRIVER),
                'applies_to':'context-only expert/router roles; acting controllers unchanged',
                'official_reference':'https://learn.chatgpt.com/docs/config-file/config-reference'}

    def describe(self):
        return {**super().describe(),'compact_context_instructions':self.compact_identity()}

    def command(self,request,schema_path):
        command=super().command(request,schema_path)
        if request.read_only:
            command[2:2]=['--config','model_instructions_file='+json.dumps(str(SYSTEM))]
        return command

    def complete(self,request):
        if self.compact_identity()!=self.frozen_compact:
            raise ValueError('Frozen compact context instructions changed')
        return super().complete(request)
