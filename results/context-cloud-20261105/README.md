# Offline cloud continuation evidence

See [the continuation record](../../docs/research/context-experiment-continuation-20261105.md).
The before-fix report retains the failing identity-compressor round trip; the
current report passes the same nine checks after correcting double serialization.
These are synthetic adapter diagnostics, with zero model calls and no Headroom
execution. They do not validate live context mutation or establish savings.

Reproduce from the repository root:

```sh
python3 tools/usage-monitor/experiments/offline_context_probe.py --output work/context-pilot-cloud-probe/offline-mechanisms.json
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_*.py'
```
