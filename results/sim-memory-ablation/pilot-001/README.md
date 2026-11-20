# Observatory SIM pilot 001

One paired optimization block, four arms, five rounds per arm, 100 independently
metered native invocations and 80 independently replayed coding grades.

The final held-out scores for C0, C1, C2 and C3 were 3/4, 2/4, 4/4 and 2/4.
C0, C1 and C2 retained identical prompt settings. Results are descriptive.
Full pilot usage was 5,859,729 tokens, $0.19191098 under the pinned API-equivalent
rates and 23 minutes 50 seconds wall time. Subscription expense is unknown.

- [Research report](../../../docs/experiments/sim-memory-ablation/report.md)
- [Measured aggregate](summary.json)
- [Arm table](conditions.csv)
- [Round decisions](rounds.csv)
- [Independent per-task outcomes](observations.jsonl)
- [Artifact checksum manifest](reproduction-manifest.json)
- [Performance plot](performance.svg) and [resource plot](resources.svg)

Durable publication summary SHA-256
`94e3343c745ab3976ec86223c38b97d3b298f93ef8a2190985084f2a77111724`.
Verified raw S3 archive ID
`6ebb73b24450094a87e983f7e1e758725bddb1dd0c5a8cd027fdabb03f13aeec`.
The private run root is `work/security/sim-memory-ablation/pilot-001`.
The committed export contains structured observations and private artifact
digests. Raw native transcripts and full candidate drafts remain local.
