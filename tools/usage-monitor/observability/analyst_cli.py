#!/usr/bin/env python3
"""TTGL analyst CLI: same tools and validation as the MCP, JSON in/out."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from analyst_mcp import handle, TOOLS
from workspace import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path(__file__).resolve().parents[3] / 'work/security/workspace')
    parser.add_argument('--codex-root', type=Path, default=Path.home()/'.codex')
    parser.add_argument('--capture-root', type=Path, default=Path(__file__).resolve().parents[3]/'work/security/langfuse-stack/captures')
    parser.add_argument('tool', choices=['tools'] + [t['name'] for t in TOOLS])
    parser.add_argument('--args', default='{}', help='JSON object, or - to read JSON from stdin')
    args = parser.parse_args()
    if args.tool == 'tools':
        print(json.dumps(TOOLS, indent=2))
        return
    try:
        arguments = json.loads(sys.stdin.read() if args.args == '-' else args.args)
        # Raw source retrieval requires only its explicit archive scope. Avoid
        # creating/migrating an analytics database in a read-only agent sandbox.
        store=(SimpleNamespace(capture_root=args.capture_root) if args.tool=='read_compression_source'
               else Store(args.data, args.codex_root, 'http://localhost:3000', args.capture_root))
        result = handle(store,
                        dict(method='tools/call', params=dict(name=args.tool, arguments=arguments)))
        for block in result.get('content', []):
            if block.get('type') == 'text':
                print(block['text'])
        if result.get('isError'):
            raise SystemExit(1)
    except (ValueError, OSError) as exc:
        print(json.dumps(dict(error=str(exc))), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
