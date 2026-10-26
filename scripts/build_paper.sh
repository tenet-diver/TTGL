#!/usr/bin/env bash
set -euo pipefail
ttgl_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ttgl_root/docs/paper"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/ttgl-paper-cache}"
mkdir -p "$XDG_CACHE_HOME"
dot -Tpng -Gdpi=180 figures/conversation.dot -o figures/conversation.png
dot -Tsvg figures/conversation.dot -o figures/conversation.svg
python - <<'PY'
from pathlib import Path
parts = ['frontmatter.md', '../thesis/personal-agent-prior-art.md', 'architecture.md',
         'methods.md', 'economics-and-results.md', 'standard-benchmark-results.md',
         'discussion-and-reproduction.md']
Path('paper.md').write_text('\n\n'.join(Path(p).read_text().rstrip() for p in parts)
                           + '\n\n# References {.unnumbered}\n\n::: {#refs}\n:::\n')
Path('references.bib').write_text('\n'.join(Path(p).read_text() for p in
    ['../thesis/references.bib', '../thesis/personal-agent-prior-art.bib', 'additional-references.bib']))
PY
pandoc paper.md --standalone --toc --number-sections --citeproc \
  --bibliography=references.bib --resource-path=. --pdf-engine=xelatex \
  -V documentclass=report -V geometry:margin=25mm -V papersize=a4 -V fontsize=11pt \
  --include-in-header=../thesis/layout.tex -V colorlinks=true -V urlcolor=blue \
  -V linkcolor=blue -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' \
  -V monofont='DejaVu Sans Mono' -o paper.pdf
pandoc paper.md --standalone --number-sections --citeproc \
  --lua-filter=docx-contents.lua \
  --reference-doc=reference.docx \
  --bibliography=references.bib --resource-path=. -o paper.docx
pandoc paper.md --standalone --toc --number-sections --citeproc \
  --bibliography=references.bib --resource-path=. --math-method=mathml \
  --css=../thesis/style.css --embed-resources -o paper.html
python - <<'PY'
import datetime, hashlib, json, subprocess
from pathlib import Path
sources = ['frontmatter.md', '../thesis/personal-agent-prior-art.md',
           '../thesis/personal-agent-prior-art-sources.json', 'architecture.md',
           'methods.md', 'economics-and-results.md', 'standard-benchmark-results.md',
           'discussion-and-reproduction.md',
           'references.bib', 'additional-references.bib', 'figures/conversation.dot',
           '../../experiments/codex-pilot-001/protocol.json',
           '../../results/codex-pilot-001/analysis/summary.json',
           '../../results/codex-pilot-001/analysis/records.json',
           '../../results/codex-pilot-001/dialogue-transcript.md',
           '../../scripts/build_paper.sh', 'docx-contents.lua', 'reference.docx',
           '../../experiments/swe-replay-001/protocol.json',
           '../../results/swe-replay-001/summary.json',
           '../../results/swe-replay-001/additional-comparisons.json',
           '../../results/swe-replay-001/figures/standalone-controls.png',
           '../../scripts/plot_swe_frontier.py']
artifacts = ['paper.md', 'paper.pdf', 'paper.docx', 'paper.html',
             'figures/conversation.png', 'figures/conversation.svg']
live_roots = [Path('../../results') / name for name in
              ['codex-isolated-20261026', 'delegation-development-001', 'delegation-heldout-001']]
completed = []
for root in live_roots:
    if not root.exists():
        continue
    for validation in sorted(root.glob('analysis*/validation.json')):
        record = json.loads(validation.read_text())
        if record.get('status') != 'completed_officially_graded_engineering_panel':
            continue
        completed.append(str(validation.parent))
        sources.extend(str(p) for p in sorted(validation.parent.rglob('*'))
                       if p.is_file() and p.suffix in ('.json', '.csv', '.md', '.txt'))
    for environment in sorted(root.glob('*/environment.json')):
        for name in ['design.json', 'design.sha256', 'environment.json', 'environment.sha256',
                     'tasks.json', 'rate-scenario.json', 'preflight.json']:
            p = environment.parent / name
            if p.is_file():
                sources.append(str(p))
sources.extend(str(p) for p in sorted(Path('../../prompts').glob('controller-v2-*.txt')))
sources.extend(['../../src/ttgl/policy.py', '../../src/ttgl/frontier.py',
                '../../scripts/run_policy_study.py', '../../scripts/report_policy_target.py'])
status = ('live_studies_in_progress_with_historical_pilot_and_replay' if not completed
          else 'completed_live_panels_with_historical_pilot_and_replay')
report = {'status':status, 'completed_live_analyses':completed,
          'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'word_count_approximate':len(Path('paper.md').read_text().split()),
          'pandoc':subprocess.check_output(['pandoc','--version'],text=True).splitlines()[0],
          'files':{p:{'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                      'bytes':Path(p).stat().st_size} for p in sources+artifacts}}
Path('build-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'words':report['word_count_approximate']}))
PY
