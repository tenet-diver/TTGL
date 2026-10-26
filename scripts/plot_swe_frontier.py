#!/usr/bin/env python3
"""Plot the published-cost replay with its essential standalone-model controls."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
source = root / "results/swe-replay-001/summary.json"
summary = json.loads(source.read_text())
rows = {p["policy"]: p for p in summary["policies"]}
output = root / "results/swe-replay-001/figures"
output.mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(10, 7))
labels = {
    "gpt_5_mini": ("GPT-5-mini", (6, -18)),
    "gpt_5_2_high": ("GPT-5.2", (-65, 10)),
    "minimax_2_5_high": ("MiniMax-M2.5", (-15, 19)),
    "kimi_k2_5_high": ("Kimi-K2.5", (-25, -18)),
    "deepseek_3_2_high": ("DeepSeek-V3.2", (-45, -18)),
    "glm_5_high": ("GLM-5", (8, -10)),
    "gemini_3_flash_high": ("Gemini-3-Flash", (-30, 15)),
    "claude_4_5_haiku_high": ("Claude-Haiku-4.5", (-44, -18)),
    "claude_4_5_sonnet_high": ("Claude-Sonnet-4.5", (-84, 12)),
    "claude_4_6_opus": ("Claude-Opus-4.6", (8, 8)),
}
for index, (model, (label, offset)) in enumerate(labels.items()):
    r = rows["always_" + model]
    x, y = r["estimated_inference_usd_per_task"], r["resolution_rate"] * 100
    ax.scatter(x, y, s=75, color="#17456b", zorder=4,
               label="Fixed single model" if index == 0 else None)
    ax.annotate(label, (x, y), xytext=offset, textcoords="offset points", fontsize=9)
for prefix, label, color, marker in [
    ("cost_benefit_router_large_", "Two-model learned allocation", "#b24c39", "o"),
    ("portfolio_lambda_", "Ten-model utility grid", "#18806e", "s"),
    ("random_expected_large_", "Expected random two-model allocation", "#999999", None),
]:
    grid = sorted((p for p in rows.values() if p["policy"].startswith(prefix)),
                  key=lambda p: p["estimated_inference_usd_per_task"])
    ax.plot([p["estimated_inference_usd_per_task"] for p in grid],
            [p["resolution_rate"] * 100 for p in grid], marker=marker,
            linewidth=1.5, color=color, label=label, alpha=.85)
primary = summary["primary_result"]
ax.scatter(primary["estimated_inference_usd_per_task"], 100 * primary["resolution_rate"],
           marker="X", s=130, color="#a5291e", zorder=6)
ax.annotate("Primary: 46.1% cheaper,\n8.6 points less accurate",
            (primary["estimated_inference_usd_per_task"], 100 * primary["resolution_rate"]),
            xytext=(23, -42), textcoords="offset points", fontsize=9,
            arrowprops={"arrowstyle": "-", "color": "#a5291e"})
oracle = rows["NONDEPLOYABLE_portfolio_outcome_cost_oracle"]
ax.scatter(oracle["estimated_inference_usd_per_task"], oracle["resolution_rate"] * 100,
           marker="*", s=150, color="#81758f", label="Outcome-aware oracle (not deployable)")
ax.annotate("87.8% oracle uses test answers",
            (oracle["estimated_inference_usd_per_task"], oracle["resolution_rate"] * 100),
            xytext=(12, -3), textcoords="offset points", fontsize=9, color="#61576b")
ax.set(xlim=(.015, .72), ylim=(53, 90),
       xlabel="Historical estimated inference USD per assigned task",
       ylabel="SWE-bench Verified tasks resolved (%)",
       title="500-task replay: compare routing with a strong inexpensive single model")
ax.grid(alpha=.18)
ax.legend(loc="lower right", fontsize=8.5, framealpha=.95)
fig.text(.12, .018, "Ten February 2026 mini-SWE-agent configurations. No fresh conversation trials. Router/infrastructure costs excluded.", fontsize=8)
fig.tight_layout(rect=(0, .035, 1, 1))
for suffix in ("png", "svg", "pdf"):
    fig.savefig(output / f"standalone-controls.{suffix}", dpi=180)
plt.close(fig)
manifest = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in output.glob("standalone-controls.*")}}
(output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
