"""Plan-based usage metering for the expensive (AI/COGS) operations.

Each metered call increments a per-user, per-day counter and is rejected with a
429 once the plan's daily limit is hit. Limits are intentionally generous on
free and effectively unlimited on pro — tune as the cost model firms up.
"""

import logging
from datetime import date

from app.db.database import engine, get_session
from app.db.models import UsageRecord
from backend.core.exceptions import QuotaExceededError

logger = logging.getLogger("finverse.api")

# metric -> per-day cap, by plan. None = unlimited.
PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "free": {"chat": 25, "report": 5},
    "pro": {"chat": 2000, "report": 500},
}
_FALLBACK = PLAN_LIMITS["free"]

# User-facing labels for the metered metrics.
METRIC_LABELS = {"chat": "AI chat messages", "report": "AI reports"}


def _limits(plan: str) -> dict[str, int | None]:
    return PLAN_LIMITS.get(plan, _FALLBACK)


class UsageService:
    def check(self, user_id: int, plan: str, metric: str) -> None:
        """Raise QuotaExceededError if the user is already at the plan's daily
        limit for `metric`. Does not increment — pair with record()."""
        limit = _limits(plan).get(metric)
        if limit is None:
            return
        UsageRecord.__table__.create(engine, checkfirst=True)
        with get_session() as s:
            row = (s.query(UsageRecord)
                   .filter_by(user_id=user_id, day=date.today(), metric=metric).first())
            if (row.count if row else 0) >= limit:
                label = METRIC_LABELS.get(metric, metric)
                raise QuotaExceededError(
                    f"Daily limit reached for {label} on the {plan} plan "
                    f"({limit}/day). Upgrade to continue."
                )

    def record(self, user_id: int, metric: str) -> None:
        """Increment today's counter for (user, metric)."""
        UsageRecord.__table__.create(engine, checkfirst=True)
        with get_session() as s:
            row = (s.query(UsageRecord)
                   .filter_by(user_id=user_id, day=date.today(), metric=metric).first())
            if row:
                row.count += 1
            else:
                s.add(UsageRecord(user_id=user_id, day=date.today(), metric=metric, count=1))

    def enforce(self, user_id: int, plan: str, metric: str) -> None:
        """check() then record() — for always-billable calls like AI chat."""
        self.check(user_id, plan, metric)
        self.record(user_id, metric)

    def usage(self, user_id: int, plan: str) -> dict:
        """Today's usage vs limits per metric (for the UI)."""
        UsageRecord.__table__.create(engine, checkfirst=True)
        with get_session() as s:
            counts = {
                r.metric: r.count for r in
                s.query(UsageRecord).filter_by(user_id=user_id, day=date.today()).all()
            }
        return {
            "plan": plan,
            "metrics": [
                {"metric": m, "label": METRIC_LABELS.get(m, m),
                 "used": counts.get(m, 0), "limit": lim}
                for m, lim in _limits(plan).items()
            ],
        }


usage_service = UsageService()
