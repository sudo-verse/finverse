import json


def save_signal(data, filename="signals.json"):
    """Persist a signal. Returns True only if it was NEW (not a uid we have
    already stored) so callers can gate side effects like Telegram alerts —
    re-processing after a restart must not re-notify.
    """
    # Database first: it owns dedup via the unique `uid` column.
    is_new = True
    try:
        from app.db.repository import save_signal_to_db
        is_new = save_signal_to_db(data)
    except Exception:
        pass  # best-effort; never breaks the engine

    if not is_new:
        return False

    # Keep the JSON file (back-compat for the legacy dashboard)
    try:
        with open(filename, "r") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    existing.append(data)

    with open(filename, "w") as f:
        json.dump(existing, f, indent=4)

    return True
