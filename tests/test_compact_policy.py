from dataclasses import replace
from pathlib import Path

import pytest
from ttgl import compact
from ttgl.personal import Request
from ttgl.policy import PolicyBackend


def request(read_only):
    return Request('fixture','fixture-model','expert' if read_only else 'controller',
                   'Fixture request.',Path('/tmp/fixture'),{},30,read_only=read_only)


def test_compaction_changes_only_context_instructions_and_preserves_tool_permissions():
    backend=compact.CompactPolicyBackend()
    normal=PolicyBackend()
    schema=Path('/tmp/schema.json')
    assert backend.command(request(False),schema)==normal.command(request(False),schema)
    contextual=backend.command(request(True),schema)
    assert contextual[2]=='--config' and 'model_instructions_file=' in contextual[3]
    assert contextual[:2]+contextual[4:]==normal.command(request(True),schema)


def test_changed_context_system_file_is_rejected_before_inference(tmp_path,monkeypatch):
    system=tmp_path/'system.txt';system.write_text('Frozen fixture instructions.')
    monkeypatch.setattr(compact,'SYSTEM',system)
    backend=compact.CompactPolicyBackend()
    system.write_text('Changed fixture instructions.')
    with pytest.raises(ValueError,match='Frozen compact'):
        backend.complete(request(True))
