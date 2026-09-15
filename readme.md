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

## Honest limitation (worth saying out loud in an interview)
The current eval rules were written to look for the exact markers this
same script injects (e.g. matching the phrase "outside the scope"), so
precision/recall come out at a suspiciously perfect 100%. That's expected
for a v1 detector, not a sign the problem is solved — it proves the
*pipeline* works end-to-end, not that the *detection logic* would catch
a real, adversarially-worded violation. A natural next step is to make
the injected violations more naturalistic (varied phrasing instead of a
fixed marker string) and see how much recall the rule-based approach
loses, which would motivate moving to an LLM-as-judge or embedding-based
detector instead of keyword rules.

## Next steps (not yet built)
- Swap the rule-based `eval_rules.py` for an LLM-as-judge evaluator that
  reads `reasoning_trace` + `agent_action` and grades compliance without
  relying on injected keyword markers
- Add a real dashboard (Streamlit or Power BI) over the DuckDB tables
- Push to GitHub as a standalone repo, separate from MidTenn Lend Map