#!/usr/bin/env python3
"""New reserved-task replay variant; original pilot grade remains frozen.

Reuses exact native/capture audit v2. New grade matches admitted Alpine profile,
task test directories and writable isolated replay; preserves original test and
data hashes. Additional tests/generated files do not fail source-only quality.
"""
from codex_team_grade_v2 import *
import argparse


def satisfies_reference_counts(stats, reference):
    return (stats['tests'] >= reference['tests'] and stats['skipped'] <= reference['skipped']
            and not stats['failures'] and not stats['errors'])


def grade(root):
    if not any((root/n).exists() for n in ('completed.json','stopped.json')):
        raise ValueError('Generation must end before independent replay')
    target=root/'independent-grade';target.mkdir(exist_ok=False)
    m=json.loads((root/'manifest.json').read_text());entry=m['base'];base=Path(entry['source'])
    if any(sha(base/p)!=v for p,v in entry['hashes'].items()):
        raise ValueError('Sealed base changed')
    actor=root/'actor';relative=m.get('src_dir','tinydb')
    source=actor/relative
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Symlink artifacts require audit; not replayed')
    shutil.copytree(base,target/'replay')
    shutil.rmtree(target/'replay'/relative)
    shutil.copytree(source,target/'replay'/relative)
    # Some libraries keep their tests inside the implementation package.
    # Restore those tests and all prepared immutable data after source copying.
    protected = list(entry.get('immutable_resources', {}))
    tests = m['test_dir'].rstrip('/')
    if tests == relative or tests.startswith(relative + '/'):
        destination = target/'replay'/tests
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(base/tests, destination)
    for path in protected:
        destination = target/'replay'/path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            raise ValueError('Protected data symlink')
        shutil.copyfile(base/path, destination)
    paths=set(entry['hashes'])|{str(p.relative_to(actor)) for p in actor.rglob('*') if p.is_file()}
    changed=[p for p in sorted(paths) if not (actor/p).is_file() or entry['hashes'].get(p)!=sha(actor/p)]
    outside=[p for p in changed if not (p==relative or p.startswith(relative+'/'))]
    unexpected=[p for p in outside if not (p.endswith('.md') and '/' not in p and p not in entry['hashes'])]
    protected_changed = [p for p in changed if p in protected or p == tests or p.startswith(tests+'/')]
    unexpected = sorted(set(unexpected + protected_changed))
    from commit0_compatibility_controls import command as test_command
    command = test_command(Path(m['runtime']), (target/'replay').resolve(), target.resolve(),
        'ttgl-grade-'+root.name, m['test_dir'], (), 'alpine311', True)[2:]
    save(target/'started.json',dict(command=command,at=datetime.now(timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),
        submitted_source_hashes={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},changed_paths=changed,excluded_changes=outside))
    with (target/'stdout.log').open('xb') as log:
        process=docker(command,stdout=log,stderr=__import__('subprocess').STDOUT,timeout=600)
    suites=list(ET.parse(target/'junit.xml').getroot().iter('testsuite')) if (target/'junit.xml').exists() else []
    stats={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    reference=json.loads(Path(entry['control_result']).read_text())['junit']
    denominator=reference['tests']-reference['skipped']
    partial=max(0,min(1,(stats['tests']-stats['skipped']-stats['failures']-stats['errors'])/denominator)) if denominator else None
    value=dict(exit_code=process.returncode,junit=stats,reference_junit=reference,
        passed=process.returncode==0 and stats['tests']>0 and satisfies_reference_counts(stats,reference),
        observed_pass_fraction=partial, restored_test_dir=tests, restored_resource_count=len(protected),
        artifact_policy_clean=not [p for p in unexpected if p in entry['hashes']],excluded_changes=outside,unexpected_changes=unexpected,
        changed_preexisting_outside_source=[p for p in unexpected if p in entry['hashes']],
        additional_outside_source=[p for p in unexpected if p not in entry['hashes']],
        scope='Prescribed public tests/resources restored from sealed base; source-only replay; additions outside implementation excluded; preexisting test/config modifications flagged separately; no hidden-test claim',model_calls=0)
    save(target/'result.json',value);print(json.dumps(value))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['grade','audit'])
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    if a.action=='grade':grade(a.root.resolve())
    else:audit(a.root.resolve())
