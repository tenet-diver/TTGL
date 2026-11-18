from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from ..experience_routing.io import read, write_new
from .routing import Policy
from .service import DelegationService


def prepare(output):
    """Inspect metadata without invoking Codex, logging credentials or pulling images."""
    source = Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex')
    missing = []
    try:
        from ..experience_routing.backend import source_binding
        binding = source_binding(source)
    except (OSError, ValueError, KeyError, TypeError):
        binding = None
        missing.append('source_local_chatgpt_account_binding')
    # Native enablement requires an operator freeze, not guessed local resources.
    missing += ['reviewed_native_worker_freeze', 'qualified_actor_and_mcp', 'finite_parent_and_campaign_budgets',
                'scoped_experience_and_capability_snapshots', 'benchmark_reservation_and_pristine_controls']
    report = {'schema_version': 1, 'stage': 'native_preparation', 'execution_ready': False,
              'source_binding_available': binding is not None, 'missing': missing,
              'new_model_calls': 0, 'automatic_retries': 0}
    write_new(Path(output)/'readiness.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description='Observatory source-scoped delegation routing')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare'); p.add_argument('--output', required=True)
    p = commands.add_parser('replay'); p.add_argument('--root', default='.'); p.add_argument('--output', required=True)
    p = commands.add_parser('serve'); p.add_argument('--config', required=True); p.add_argument('--native-freeze')
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.output), indent=2))
    elif args.command == 'replay':
        from .replay import historical_replay
        result = historical_replay(args.root, args.output)
        print(json.dumps({k: {n: v for n, v in values.items() if n != 'rows'} for k, values in result['arms'].items()}, indent=2))
    elif args.command == 'serve':
        from .mcp import serve
        cfg = read(args.config)
        # Route-only by default. Native attachment uses a fixed reviewed adapter,
        # never an arbitrary executable/factory supplied in a JSON document.
        worker = None
        if args.native_freeze:
            from .native import worker_from_freeze
            worker = worker_from_freeze(args.native_freeze, service_config=cfg)
        service = DelegationService(context=cfg['context'], experiences=read(cfg['experiences']),
            models=read(cfg['models']), policy=Policy(**cfg.get('policy', {})), output=cfg['output'], worker=worker)
        try:
            serve(service)
        finally:
            service.close()


if __name__ == '__main__':
    main()
