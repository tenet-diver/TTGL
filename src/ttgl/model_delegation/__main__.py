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
    p = commands.add_parser('qualify-transport'); p.add_argument('--protocol', required=True); p.add_argument('--output', required=True)
    p.add_argument('--source-home', default=os.environ.get('CODEX_HOME') or str(Path.home()/'.codex'))
    p.add_argument('--root', default='.')
    p = commands.add_parser('build-snapshots'); p.add_argument('--config', required=True); p.add_argument('--output', required=True)
    p = commands.add_parser('build-campaign'); p.add_argument('--config', required=True); p.add_argument('--output', required=True)
    p.add_argument('--comparison', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.output), indent=2))
    elif args.command == 'qualify-transport':
        from .qualification import qualify_transport
        print(json.dumps(qualify_transport(args.root, args.output, source_home=args.source_home, protocol=args.protocol), indent=2))
    elif args.command == 'build-snapshots':
        from .accumulation import build_snapshots
        cfg = read(args.config)
        result = build_snapshots(read(cfg['partitions']), read(cfg['records']), prefixes=tuple(cfg['prefixes']),
                                 scope=cfg['scope'], watermark=cfg['watermark'])
        write_new(Path(args.output)/'snapshots.json', result)
        print(json.dumps({'snapshots': len(result['snapshots']), 'excluded': len(result['excluded']), 'model_calls': 0}))
    elif args.command == 'build-campaign':
        from .accumulation import build_campaign, build_comparison_campaign
        cfg = read(args.config)
        common = dict(points=tuple(cfg['points']), limits=cfg['limits'], source_pins=cfg['source_pins'],
                      baseline_pins=cfg['baseline_pins'], stage=cfg['stage'])
        if args.comparison:
            result = build_comparison_campaign(read(cfg['partitions']), read(cfg['snapshots'])['snapshots'], **common)
        else:
            result = build_campaign(read(cfg['partitions']), read(cfg['snapshots'])['snapshots'], systems=tuple(cfg['systems']), **common)
        write_new(Path(args.output)/'campaign.json', result)
        print(json.dumps({'campaign_id': result['campaign_id'], 'assignments': len(result['assignments']),
                          'maximum_totals': result['maximum_totals'], 'model_calls': 0}))
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
