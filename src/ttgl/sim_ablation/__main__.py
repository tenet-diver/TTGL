"""Run or resume the Observatory SIM memory ablation."""
import argparse
from pathlib import Path

from ..experience_routing.io import read
from .memory import CONDITIONS, freeze_bank, read_bank
from .study import MODEL, ROOT, execute, load_protocol, matrix_lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "experiments/sim-memory-ablation/pilot-001.json")
    parser.add_argument("--bank", type=Path, default=ROOT / "experiments/sim-memory-ablation/history-001.json")
    parser.add_argument("--run", type=Path, help="Private run directory under work/security")
    actions = parser.add_subparsers(dest="command", required=True)
    actions.add_parser("historical", help="Reconcile source observations and freeze historical memory")
    actions.add_parser("check", help="Check empty and reference submissions with the independent grader")
    for command in ("matrix", "resume"):
        subparser = actions.add_parser(command)
        subparser.add_argument("--condition", choices=CONDITIONS)
        subparser.add_argument("--phase", choices=("all", "optimization", "heldout"), default="all")
    for command in ("analyze", "export"):
        subparser = actions.add_parser(command)
        subparser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "historical":
        bank = freeze_bank(ROOT, args.bank)
        print(f"Frozen {len(bank['records'])} records, SHA-256 {bank['sha256']}")
        return
    if args.command == "check":
        from .benchmark import evaluate, load_tasks
        for task in load_tasks().values():
            reference, empty = evaluate(task, task.reference), evaluate(task, task.starter)
            if not reference.passed or empty.passed:
                raise RuntimeError(f"Bad reference or empty control for {task.id}")
            print(f"{task.id} {task.split} reference {reference.passed_checks}/{reference.total_checks}, starter {empty.passed_checks}/{empty.total_checks}")
        return
    if not args.run:
        parser.error("--run is required")
    run = args.run.resolve()
    if args.command in ("analyze", "export"):
        from .analysis import report
        report(run, args.output, reproduce=args.command == "export")
        return
    from .runtime import NativeRuntime
    if not run.is_relative_to((ROOT / "work/security").resolve()):
        parser.error("Native artifacts belong in the private work/security tree")
    if args.condition and args.phase != "optimization":
        parser.error("Use --phase optimization for an individual condition")
    protocol = load_protocol(args.protocol)
    bank = read_bank(args.bank)
    with matrix_lock(run):
        runtime = NativeRuntime(ROOT, run, effort=protocol["effort"],
                                timeout_seconds=protocol["timeout_seconds"], rates={MODEL: protocol["rates"]})
        execute(runtime, run, protocol, bank, condition=args.condition, phase=args.phase)


if __name__ == "__main__":
    main()
