"""
Step 3: load the synthetic agent_logs into DuckDB with an explicit schema,
mirroring how you'd land raw logs in a real warehouse before running
governance checks on top.
"""

import os
import duckdb

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "agent_logs.json")
DB_PATH = os.path.join(HERE, "..", "data", "governance.duckdb")

con = duckdb.connect(DB_PATH)

con.execute("DROP TABLE IF EXISTS agent_logs")
con.execute(
    f"""
    CREATE TABLE agent_logs AS
    SELECT
        log_id,
        agent_id,
        session_id,
        CAST(timestamp AS TIMESTAMP) AS timestamp,
        task_type,
        user_instruction,
        agent_action,
        reasoning_trace,
        requested_shutdown,
        complied_with_stop,
        exposed_reasoning,
        flag_violation,
        violation_type
    FROM read_json_auto('{DATA_PATH}')
    """
)

count = con.execute("SELECT COUNT(*) FROM agent_logs").fetchone()[0]
print(f"Loaded {count} rows into {DB_PATH}")

print("\nSchema:")
print(con.execute("DESCRIBE agent_logs").fetchdf())

print("\nViolation rate by task_type:")
print(
    con.execute(
        """
        SELECT task_type,
               COUNT(*) AS n,
               SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) AS violations,
               ROUND(100.0 * SUM(CASE WHEN flag_violation THEN 1 ELSE 0 END) / COUNT(*), 1) AS violation_pct
        FROM agent_logs
        GROUP BY task_type
        ORDER BY violation_pct DESC
        """
    ).fetchdf()
)

con.close()