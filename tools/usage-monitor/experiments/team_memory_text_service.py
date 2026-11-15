#!/usr/bin/env python3
"""Versioned service entry point for the isolated, reviewed text-only runtime.

The frozen MCP broker/backends execute unchanged. Only public dependency/model
asset roots change; original memory runtime and other workers remain untouched.
"""
import argparse
import json
import os
from pathlib import Path
import sys


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['serve']);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();config=json.loads(a.config.read_text())
    root=Path(os.environ['TTGL_TEAM_TEXT_RUNTIME']).resolve()
    import team_memory_backends
    team_memory_backends.GLOBAL=root
    if config['kind']=='mem0_luna':
        import repository_mem0_luna
        repository_mem0_luna.GLOBAL=root
    elif config['kind']=='graphiti_luna':
        import repository_graphiti_luna
        repository_graphiti_luna.GLOBAL=root
    from team_memory_service import serve
    os.umask(0o077);serve(config)
