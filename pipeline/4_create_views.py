"""Create analytical SQLite views for brand visibility metrics."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.db import get_connection, init_db


def create_views() -> None:
    with get_connection() as conn:
        init_db(conn)
        conn.executescript(
            """
            DROP VIEW IF EXISTS view_share_of_model;
            DROP VIEW IF EXISTS view_brand_sentiment;

            CREATE VIEW view_share_of_model AS
            SELECT
                rr.model_name AS model_name,
                pm.top_brand AS brand,
                COUNT(*) AS win_count,
                ROUND(
                    100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY rr.model_name),
                    2
                ) AS win_rate_pct
            FROM parsed_metrics pm
            INNER JOIN raw_responses rr ON rr.id = pm.response_id
            WHERE rr.status = 'success'
            GROUP BY rr.model_name, pm.top_brand;

            CREATE VIEW view_brand_sentiment AS
            SELECT
                pm.top_brand AS brand,
                ROUND(AVG(pm.sentiment), 4) AS avg_sentiment,
                COUNT(*) AS sample_size
            FROM parsed_metrics pm
            GROUP BY pm.top_brand;
            """
        )
        conn.commit()
        print("Created views: view_share_of_model, view_brand_sentiment")


if __name__ == "__main__":
    create_views()
