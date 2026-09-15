"""
Step 5: a lightweight observability summary -- the kind of rollup you'd
put on a monitoring dashboard (Power BI / Streamlit) to track governance
health over time, per agent, and by violation type.
"""

import os
import duckdb

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "..", "data", "governance.duckdb")

con = duckdb.connect(DB_PATH)

print("=== Daily violation trend ===")
print(
    con.execute(
        """
        SELECT
            CAST(timestamp AS DATE) AS day,
            COUNT(*) AS total_logs,
            SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) AS violations,
            ROUND(100.0 * SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) / COUNT(*), 1) AS violation_pct
        FROM agent_logs
        GROUP BY day
        ORDER BY day
        LIMIT 10
        """
    ).fetchdf()
)

print("\n=== Per-agent violation rate (flags any agent above dataset average) ===")
print(
    con.execute(
        """
        WITH agent_stats AS (
            SELECT
                agent_id,
                COUNT(*) AS n,
                SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) AS violations,
                ROUND(100.0 * SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) / COUNT(*), 1) AS violation_pct
            FROM agent_logs
            GROUP BY agent_id
        ),
        overall AS (
            SELECT ROUND(100.0 * SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) / COUNT(*), 1) AS avg_pct
            FROM agent_logs
        )
        SELECT agent_stats.*, overall.avg_pct,
               (agent_stats.violation_pct > overall.avg_pct) AS above_average
        FROM agent_stats, overall
        ORDER BY violation_pct DESC
        """
    ).fetchdf()
)

print("\n=== Shutdown compliance rate (critical governance metric) ===")
print(
    con.execute(
        """
        SELECT
            COUNT(*) AS shutdown_requests,
            SUM(CASE WHEN complied_with_stop THEN 1 ELSE 0 END) AS complied,
            ROUND(100.0 * SUM(CASE WHEN complied_with_stop THEN 1 ELSE 0 END) / COUNT(*), 1) AS compliance_pct
        FROM agent_logs
        WHERE requested_shutdown
        """
    ).fetchdf()
)

con.close()
