#!/usr/bin/env bash
set -euo pipefail
ttgl_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ttgl_root/docs/thesis"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${TMPDIR:-/tmp}/ttgl-document-cache}"
mkdir -p "$XDG_CACHE_HOME"
for ttgl_program in pandoc xelatex dot; do
  command -v "$ttgl_program" >/dev/null || {
    echo "Required document tool is missing: $ttgl_program" >&2
    exit 1
  }
done
dot -Tpng -Gdpi=180 figures/architecture.dot -o figures/architecture.png
dot -Tsvg figures/architecture.dot -o figures/architecture.svg
python - <<'PY'
from pathlib import Path
chapters = [
    'frontmatter.md', 'introduction.md', 'literature.md', 'agent-learning-evidence.md',
    'system-design.md', 'personal-controller.md', 'longitudinal-learning.md',
    'model-landscape.md', 'accuracy-context.md', 'task-economics.md',
    'browser-domain.md', 'adaptation-and-switching.md', 'ensemble-methodology.md',
    'methodology.md', 'analysis-plan.md',
    'reproducibility-and-limits.md',
]
text = '\n\n'.join(Path(p).read_text().rstrip() for p in chapters)
text += '\n\n# References {.unnumbered}\n\n::: {#refs}\n:::\n'
Path('thesis.md').write_text(text)
PY
pandoc thesis.md --standalone --toc --number-sections --citeproc \
  --bibliography=references.bib --resource-path=. \
  --pdf-engine=xelatex -V documentclass=report \
  -V geometry:margin=25mm -V papersize=a4 -V fontsize=11pt \
  --include-in-header=layout.tex \
  -V colorlinks=true -V urlcolor=blue -V linkcolor=blue \
  -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' \
  -V monofont='DejaVu Sans Mono' -o thesis.pdf
pandoc thesis.md --standalone --toc --number-sections --citeproc \
  --bibliography=references.bib --resource-path=. -o thesis.docx
pandoc thesis.md --standalone --toc --number-sections --citeproc \
  --bibliography=references.bib --resource-path=. --mathml \
  --css=style.css --embed-resources -o thesis.html
python - <<'PY'
import datetime, hashlib, json, subprocess
from pathlib import Path
names = ['thesis.md', 'thesis.pdf', 'thesis.docx', 'thesis.html', 'references.bib',
         'model-catalog.csv', 'market-sources.json', 'accuracy-context-sources.json',
         'frontmatter.md', 'introduction.md', 'literature.md', 'system-design.md',
         'model-landscape.md', 'accuracy-context.md', 'methodology.md',
         'analysis-plan.md', 'reproducibility-and-limits.md', 'layout.tex',
         'style.css', 'figures/architecture.dot', 'figures/architecture.png',
         'figures/architecture.svg', 'evidence-audit.json', 'evidence-audit-details.json',
         'task-economics.md', 'task-price-comparisons.csv', 'task-price-scenarios.csv',
         'task-economics-sources.json', 'task-price-checks.json', 'browser-domain.md',
         'browser-sources.json', 'adaptation-and-switching.md', 'adaptation-sources.json',
         'ensemble-methodology.md', 'ensemble-methods-sources.json', 'portfolio-review.json',
         'agent-learning-evidence.md', 'agent-learning-sources.json',
         'personal-controller.md', 'controller-sources.json', 'personal-review.json',
         'longitudinal-learning.md', 'longitudinal-plan.json',
         '../../scripts/build_task_price_table.py', '../../scripts/build_thesis.sh']
report = {
    'status': 'pre_results_manuscript',
    'built_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pandoc': subprocess.check_output(['pandoc','--version'], text=True).splitlines()[0],
    'word_count_approximate': len(Path('thesis.md').read_text().split()),
    'artifacts': {name: {'bytes':Path(name).stat().st_size,
                       'sha256':hashlib.sha256(Path(name).read_bytes()).hexdigest()} for name in names},
}
Path('build-manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status':report['status'],'words':report['word_count_approximate']},indent=2))
PY
