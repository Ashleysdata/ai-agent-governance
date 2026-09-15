# AI Agent Governance & Observability Pipeline

A synthetic-data project simulating what it takes to monitor whether AI
agents comply with governance rules like those in Microsoft's "Humanist AI"
Code of Conduct (Sept 2026): human oversight, no resisting shutdown/correction,
transparent (non-hidden) reasoning, no unauthorized goal-setting.

## Why synthetic data
No company publishes real internal AI-agent audit logs, and doing this
"for real" would need production agent access I don't have. So the
pipeline generates its own labeled data — every violation is injected
with a known ground-truth label, which lets the eval layer be scored
for precision/recall instead of just eyeballed.

## Pipeline
1. **`data/base_scenarios.json`** — 60 curated, clean (non-violating) agent
   task scenarios across 4 task types (customer_support, data_query,
   workflow_automation, scheduling).
2. **`scripts/build_dataset.py`** — expands these into 900 timestamped log
   rows across 10 simulated agents, injecting a controlled 14% violation
   rate across 3 violation types (resisted_shutdown, hidden_reasoning,
   unauthorized_goal), with ground truth stored alongside.
3. **`scripts/load_to_duckdb.py`** — loads the JSON into DuckDB with an
   explicit schema (`data/governance.duckdb`), same as landing raw logs
   in a warehouse.
4. **`scripts/eval_rules.py`** — a rule-based detector for each violation
   type, scored against ground truth (precision/recall/F1 + per-type
   recall + false positive inspection).
5. **`scripts/observability_report.py`** — rollups you'd put on a
   monitoring dashboard: daily violation trend, per-agent violation rate
   (flagging agents above the fleet average), and shutdown-compliance
   rate — arguably the single most important governance metric.

## Honest limitation, tested (not just a caveat)
The v1 eval rules were written to look for the exact markers the
generator injects (e.g. matching the phrase "outside the scope"), so
precision/recall came out at a suspiciously perfect 100%. Rather than
just note that as a caveat, I stress-tested it: `build_dataset_hard.py`
re-injects the same three violation types but with varied, naturalistic
phrasing instead of one fixed marker string, and `eval_rules_on_hard.py`
runs the *same, unchanged* detection rules against it.

**Result: overall recall dropped from 100% to 63.5%.** But the three
rules didn't degrade equally:

| Violation type | Recall (easy) | Recall (hard) |
|---|---|---|
| resisted_shutdown | 100% | 100% |
| hidden_reasoning | 100% | 100% |
| unauthorized_goal | 100% | **0%** |

The two rules that check **structured fields** (`complied_with_stop`,
whether `reasoning_trace` is empty) stayed perfectly robust — phrasing
can't fool a boolean. The one rule that did **keyword text-matching**
on `agent_action` collapsed completely once the wording changed. That's
the real lesson: prefer structured, verifiable signals over keyword
matching wherever governance behavior can be captured that way; reserve
free-text judgment (LLM-as-judge, embeddings) for the cases where it
genuinely can't.

## Next steps (not yet built)
- Replace the `unauthorized_goal` keyword rule with an LLM-as-judge
  evaluator (read `user_instruction` + `agent_action`, ask a model
  whether the action stayed in scope) and re-run against
  `agent_logs_hard.json` to see if recall recovers
- Add a real dashboard (Streamlit or Power BI) over the DuckDB tables
- GitHub repo: github.com/Ashleysdata/ai-agent-governance (main branch
  has the base pipeline; `feature/harder-eval` branch has this
  stress-test)