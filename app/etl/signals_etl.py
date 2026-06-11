"""ETL: migrate existing signals.json rows into the `news_signals` table.

Going forward the live engine writes signals straight to the DB; this backfills
whatever was accumulated in the flat file before the DB existed.
"""

import hashlib
import json

from app.db.repository import save_signal_to_db
from app.utils.logger import logger

SIGNALS_FILE = "signals.json"


def _make_uid(row):
    """Older rows have no uid — derive a stable one from their content."""
    raw = f"{row.get('source')}|{row.get('ticker')}|{row.get('time')}|{row.get('news')}"
    return "legacy:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def run(path=SIGNALS_FILE):
    try:
        with open(path, "r") as f:
            rows = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"signals_etl: cannot read {path}: {e}")
        return 0

    inserted = 0
    for row in rows:
        if "uid" not in row or not row["uid"]:
            row = {**row, "uid": _make_uid(row)}
        if save_signal_to_db(row):
            inserted += 1

    logger.info(f"signals_etl: inserted {inserted} new signals (of {len(rows)} rows)")
    return inserted


if __name__ == "__main__":
    run()
