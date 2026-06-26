"""Schema for the Market Mood Index — one market-wide fear↔greed read."""

from backend.schemas.common import APIModel


class MoodComponent(APIModel):
    label: str
    value: float          # 0-100 sub-reading


class MarketMoodOut(APIModel):
    value: float          # 0-100 composite (0 = extreme fear, 100 = extreme greed)
    zone: str             # Extreme Fear | Fear | Neutral | Greed | Extreme Greed
    components: list[MoodComponent] = []
    sample: int = 0       # number of stocks that contributed
