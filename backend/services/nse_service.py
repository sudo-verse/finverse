"""Live NSE data — wraps the existing NSEClient.quote_api() (app.market).

Adds a small TTL cache so page loads don't hammer NSE (which rate-limits and
expires cookies aggressively), and maps raw payloads onto the API schemas.
"""

import logging
import threading
import time
from typing import Any

from backend.core.exceptions import ServiceUnavailableError
from backend.schemas.nse import (
    AnnouncementOut,
    AnnualReportOut,
    BrsrOut,
    CompanyProfile,
    CorpActionOut,
    CorpEventOut,
    GiftNiftyQuote,
    HoldingCategory,
    IndexQuote,
    IntradayPoint,
    IntradaySeries,
    LiveQuote,
    MarketMovers,
    MarketOverview,
    MarqueeItem,
    MoverOut,
    NsePeerOut,
    TurnoverRow,
    PerformanceRow,
    QuarterlyResultOut,
    QuarterOption,
    ShareholdingPeriod,
    UsdInrQuote,
)

logger = logging.getLogger("finverse.api")

QUOTE_TTL = 30  # seconds — live quote / peers
CORPORATE_TTL = 600  # seconds — filings change rarely


def _num(value: Any) -> float | None:
    """NSE mixes numbers, numeric strings, '-' and nulls."""
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class NSEService:
    def __init__(self) -> None:
        self._client = None
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, Any]] = {}

    def _get_client(self):
        """Lazy singleton — NSEClient does a network handshake on init."""
        with self._lock:
            if self._client is None:
                from app.market.nse_client import NSEClient

                self._client = NSEClient()
            return self._client

    def _call(self, function_name: str, ttl: int, _api: str = "quote", **params: Any) -> Any:
        key = f"{_api}:{function_name}:{sorted(params.items())}"
        now = time.time()
        hit = self._cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]

        client = self._get_client()
        fetch = {"quote": client.quote_api, "client": client.next_api, "home": client.home_api}[_api]
        data = fetch(function_name, **params)
        if data is None:
            if hit:  # serve stale data over an error
                logger.warning("nse: %s failed, serving stale cache", function_name)
                return hit[1]
            raise ServiceUnavailableError(
                f"NSE live data unavailable ({function_name}). Try again shortly."
            )
        self._cache[key] = (now, data)
        return data

    # ------------------------------------------------------------------ quote

    def live_quote(self, symbol: str) -> LiveQuote:
        data = self._call(
            "getSymbolData", QUOTE_TTL, marketType="N", series="EQ", symbol=symbol
        )
        rows = data.get("equityResponse") if isinstance(data, dict) else None
        if not rows:
            raise ServiceUnavailableError(f"NSE returned no quote for {symbol}.")
        row = rows[0]
        meta = row.get("metaData", {})
        trade = row.get("tradeInfo", {})
        book = row.get("orderBook", {})

        last_price = _num(trade.get("lastPrice")) or _num(book.get("lastPrice"))
        issued = _num(trade.get("issuedSize"))
        return LiveQuote(
            symbol=meta.get("symbol", symbol),
            company_name=meta.get("companyName"),
            isin=meta.get("isinCode"),
            last_price=last_price,
            change=_num(meta.get("change")),
            p_change=_num(meta.get("pChange")),
            open=_num(meta.get("open")),
            day_high=_num(meta.get("dayHigh")),
            day_low=_num(meta.get("dayLow")),
            previous_close=_num(meta.get("previousClose")),
            average_price=_num(meta.get("averagePrice")),
            total_traded_volume=_num(trade.get("totalTradedVolume")),
            total_traded_value=_num(trade.get("totalTradedValue")),
            market_cap=(last_price * issued) if (last_price and issued) else None,
            free_float_market_cap=_num(trade.get("ffmc")),
            issued_size=issued,
            face_value=_num(trade.get("faceValue")),
            delivery_to_traded=_num(trade.get("deliveryToTradedQuantity")),
        )

    # -------------------------------------------------------------- corporate

    def announcements(self, symbol: str, limit: int = 10) -> list[AnnouncementOut]:
        data = self._call(
            "getCorporateAnnouncement", CORPORATE_TTL,
            symbol=symbol, marketApiType="equities", noOfRecords=limit,
        )
        return [
            AnnouncementOut(
                subject=r.get("desc"),
                details=(r.get("attchmntText") or "")[:600] or None,
                attachment_url=r.get("attchmntFile"),
                broadcast_at=r.get("an_dt"),
                industry=r.get("smIndustry"),
            )
            for r in (data or [])
        ]

    def corporate_actions(self, symbol: str, limit: int = 10) -> list[CorpActionOut]:
        data = self._call(
            "getCorpAction", CORPORATE_TTL,
            symbol=symbol, marketApiType="equities", noOfRecords=limit,
        )
        return [
            CorpActionOut(
                subject=r.get("subject"),
                ex_date=r.get("exDate"),
                record_date=r.get("recDate"),
                series=r.get("series"),
                face_value=r.get("faceVal"),
            )
            for r in (data or [])
        ]

    def annual_reports(self, symbol: str, limit: int = 10) -> list[AnnualReportOut]:
        data = self._call(
            "getCorpAnnualReport", CORPORATE_TTL,
            symbol=symbol, marketApiType="equities", noOfRecords=limit,
        )
        return [
            AnnualReportOut(
                company_name=r.get("companyName"),
                from_year=r.get("fromYr"),
                to_year=r.get("toYr"),
                broadcast_at=r.get("broadcast_dttm"),
                file_url=r.get("fileName"),
                file_size=r.get("attFileSize"),
            )
            for r in (data or [])
        ]

    def events(self, symbol: str, limit: int = 5) -> list[CorpEventOut]:
        data = self._call(
            "getCorpEventCalender", CORPORATE_TTL,
            symbol=symbol, noOfRecords=limit, marketApiType="equities",
        )
        return [self._event(r) for r in (data or [])]

    def board_meetings(self, symbol: str, limit: int = 10) -> list[CorpEventOut]:
        data = self._call(
            "getCorpBoardMeeting", CORPORATE_TTL,
            symbol=symbol, marketApiType="equities", type="W", noOfRecords=limit,
        )
        return [self._event(r) for r in (data or [])]

    @staticmethod
    def _event(r: dict) -> CorpEventOut:
        return CorpEventOut(
            date=r.get("bm_date"),
            purpose=r.get("bm_desc") if len(r.get("bm_desc") or "") < 120 else r.get("bm_purpose"),
            description=r.get("bm_purpose") if len(r.get("bm_desc") or "") < 120 else r.get("bm_desc"),
            attachment_url=r.get("attachment"),
            announced_at=r.get("bm_timestamp"),
        )

    def quarterly_results(self, symbol: str) -> list[QuarterlyResultOut]:
        data = self._call("getFinancialStatus", CORPORATE_TTL, symbol=symbol)
        return [
            QuarterlyResultOut(
                period=r.get("to_date_MonYr"),
                to_date=r.get("to_date"),
                audited=r.get("audited"),
                total_income=_num(r.get("totalIncome")),
                profit_before_tax=_num(r.get("reProLossBefTax")),
                net_profit=_num(r.get("netProLossAftTax")),
                eps=_num(r.get("eps")),
                broadcast_at=r.get("re_broadcast_timestamp"),
            )
            for r in (data or [])
        ]

    # ----------------------------------------------------------------- market

    @staticmethod
    def _index_quote(r: dict) -> IndexQuote:
        return IndexQuote(
            name=r.get("indexName", "?"),
            last=_num(r.get("last")),
            perc_change=_num(r.get("percChange")),
            open=_num(r.get("open")),
            high=_num(r.get("high")),
            low=_num(r.get("low")),
            previous_close=_num(r.get("previousClose")),
            year_high=_num(r.get("yearHigh")),
            year_low=_num(r.get("yearLow")),
            time=r.get("timeVal"),
        )

    def market_overview(self) -> MarketOverview:
        """homeApi getIndicesData + getGiftNifty + getPreOpenMarketStatus."""
        indices: list[IndexQuote] = []
        gift = usd = mcap = status = None

        try:
            data = self._call("getIndicesData", QUOTE_TTL, _api="home")
            indices = [self._index_quote(r) for r in (data or {}).get("data") or []]
        except ServiceUnavailableError:
            pass

        try:
            data = (self._call("getGiftNifty", QUOTE_TTL, _api="client") or {}).get("data") or {}
            g = data.get("giftNifty") or {}
            gift = GiftNiftyQuote(
                last_price=_num(g.get("lastprice")),
                day_change=_num(g.get("daychange")),
                per_change=_num(g.get("perchange")),
                expiry=g.get("expirydate"),
                time=g.get("timestmp"),
            )
            u = data.get("usdInr") or {}
            usd = UsdInrQuote(ltp=_num(u.get("ltp")), updated_time=u.get("updated_time"), expiry=u.get("expiry_dt"))
            mcap = _num((data.get("marketCapitalization") or {}).get("tlMKtCapLacCr"))
        except ServiceUnavailableError:
            pass

        try:
            status = (self._call("getPreOpenMarketStatus", QUOTE_TTL) or {}).get("marketStatus")
        except ServiceUnavailableError:
            pass

        if not indices and gift is None:
            raise ServiceUnavailableError("NSE market data unavailable. Try again shortly.")

        return MarketOverview(
            indices=indices,
            gift_nifty=gift,
            usd_inr=usd,
            total_market_cap_lac_cr=mcap,
            market_status=status,
        )

    def movers(self) -> MarketMovers:
        data = self._call("getTopTenStock", QUOTE_TTL)

        def rows(key: str) -> list[MoverOut]:
            return [
                MoverOut(
                    symbol=r.get("symbol", "?"),
                    last_price=_num(r.get("lastPrice")),
                    change=_num(r.get("change")),
                    p_change=_num(r.get("pchange")),
                    previous_close=_num(r.get("previousClose")),
                    traded_volume=_num(r.get("totalTradedVolume")),
                    traded_value=_num(r.get("totalTradedValue")),
                )
                for r in (data or {}).get(key) or []
            ]

        return MarketMovers(
            gainers=rows("topGainers"),
            losers=rows("topLoosers"),  # sic — NSE's key is misspelled
            most_active=rows("mostActiveValue"),
            timestamp=(data or {}).get("timestamp"),
        )

    def block_deals(self) -> Any:
        """Raw block-deal session windows (shape varies; often empty)."""
        return (self._call("getBlockDealSession", QUOTE_TTL) or {}).get("data") or {}

    def all_indices(self) -> list[IndexQuote]:
        """getIndexData type=All — every NSE index with live quotes."""
        data = self._call("getIndexData", QUOTE_TTL, _api="client", type="All")
        return [self._index_quote(r) for r in (data or {}).get("data") or []]

    def index_chart(self, index: str, flag: str = "1D") -> IntradaySeries:
        """getGraphChart — intraday tick series for an index."""
        data = self._call("getGraphChart", QUOTE_TTL, _api="client", type=index, flag=flag)
        payload = (data or {}).get("data") or {}
        points = [
            IntradayPoint(time=int(p[0]), price=float(p[1]))
            for p in payload.get("grapthData") or []
            if isinstance(p, (list, tuple)) and len(p) >= 2 and p[1] is not None
        ]
        return IntradaySeries(symbol=payload.get("name") or index, points=points)

    def marquee(self) -> list[MarqueeItem]:
        """getMarqueData — NIFTY 50 constituents ticker."""
        data = self._call("getMarqueData", QUOTE_TTL, _api="client")
        return [
            MarqueeItem(
                symbol=r.get("symbol", "?"),
                last_price=_num(r.get("lastTradedPrice")),
                change=_num(r.get("change")),
                per_change=_num(r.get("perChange")),
            )
            for r in (data or {}).get("data") or []
        ]

    def turnover(self) -> list[TurnoverRow]:
        """getMarketTurnoverSummary — segment-wise turnover (equities only)."""
        data = self._call("getMarketTurnoverSummary", QUOTE_TTL, _api="client")
        return [
            TurnoverRow(
                segment=r.get("segment"),
                instrument=r.get("instrument"),
                turnover=_num(r.get("notionalTurnover")),
                trades=_num(r.get("noOfTrades")),
                volume=_num(r.get("volume")),
                prev_turnover=_num(r.get("prevNotionalTurnover")),
                timestamp=r.get("mktTimeStamp"),
            )
            for r in ((data or {}).get("data") or {}).get("equities") or []
        ]

    # ------------------------------------------------------------ stock extras

    def intraday(self, symbol: str, days: str = "1D") -> IntradaySeries:
        """getSymbolChartData — identifier is `<symbol>EQN` for NSE equities."""
        data = self._call(
            "getSymbolChartData", QUOTE_TTL, symbol=f"{symbol}EQN", days=days
        )
        points = [
            IntradayPoint(time=int(p[0]), price=float(p[1]))
            for p in (data or {}).get("grapthData") or []
            if isinstance(p, (list, tuple)) and len(p) >= 2 and p[1] is not None
        ]
        return IntradaySeries(symbol=symbol, points=points)

    def shareholding(self, symbol: str, limit: int = 5) -> list[ShareholdingPeriod]:
        data = self._call(
            "getShareholdingPattern", CORPORATE_TTL, symbol=symbol, noOfRecords=limit
        )
        periods: list[ShareholdingPeriod] = []
        for date_key, payload in (data or {}).items():
            if not isinstance(payload, dict):
                continue
            holdings = [
                HoldingCategory(category=v["name"], pct=_num(v.get("value")))
                for v in payload.values()
                if isinstance(v, dict) and v.get("name")
            ]
            if holdings:
                periods.append(ShareholdingPeriod(date=date_key, holdings=holdings))
        return periods

    PERFORMANCE_PERIODS = [
        ("1W", "one_week_chng_per"),
        ("1M", "one_month_chng_per"),
        ("3M", "three_month_chng_per"),
        ("6M", "six_month_chng_per"),
        ("1Y", "one_year_chng_per"),
        ("2Y", "two_year_chng_per"),
        ("3Y", "three_year_chng_per"),
        ("5Y", "five_year_chng_per"),
    ]

    def performance(self, symbol: str) -> list[PerformanceRow]:
        """getYearwiseData — stock vs index % change over standard windows."""
        data = self._call("getYearwiseData", CORPORATE_TTL, symbol=f"{symbol}EQN")
        row = data[0] if isinstance(data, list) and data else {}
        return [
            PerformanceRow(
                period=label,
                stock=_num(row.get(key)),
                index=_num(row.get(f"index_{key}")),
            )
            for label, key in self.PERFORMANCE_PERIODS
        ]

    def profile(self, symbol: str) -> CompanyProfile:
        """getMetaData + getIndexList + getRegDetails + about text."""
        meta = self._call("getMetaData", CORPORATE_TTL, symbol=symbol) or {}

        indices: list[str] = []
        try:
            data = self._call("getIndexList", CORPORATE_TTL, symbol=symbol)
            indices = [i for i in data if isinstance(i, str)] if isinstance(data, list) else []
        except ServiceUnavailableError:
            pass

        about = None
        try:
            data = self._call("getPeerComparisonAboutCompany", CORPORATE_TTL, symbol=symbol)
            about = (data or {}).get("data") or None
        except ServiceUnavailableError:
            pass

        status = None
        try:
            data = self._call("getRegDetails", CORPORATE_TTL, symbol=symbol)
            if isinstance(data, list) and data:
                status = data[0].get("status")
        except ServiceUnavailableError:
            pass

        def flag(key: str) -> bool:
            return str(meta.get(key, "")).lower() == "true"

        return CompanyProfile(
            symbol=meta.get("symbol", symbol),
            company_name=meta.get("companyName"),
            isin=meta.get("isin"),
            active_series=meta.get("activeSeries") or [],
            is_fno=flag("isFNOSec"),
            is_slb=flag("isSLBSec"),
            is_etf=flag("isETFSec"),
            is_suspended=flag("isSuspended"),
            listing_status=status,
            indices=indices,
            about=about,
        )

    def brsr(self, symbol: str) -> list[BrsrOut]:
        data = self._call("getCorpBrsr", CORPORATE_TTL, symbol=symbol)
        return [
            BrsrOut(
                fy_from=str(r.get("fyFrom") or ""),
                fy_to=str(r.get("fyTo") or ""),
                attachment_url=r.get("attachmentFile"),
                file_size=r.get("attachedFileSize"),
                submitted_at=r.get("submissionDate"),
            )
            for r in (data or [])
        ]

    def peer_quarters(self, symbol: str) -> list[QuarterOption]:
        data = self._call("getPeerComparisonQuaters", CORPORATE_TTL, symbol=symbol)
        return [
            QuarterOption(label=r.get("label", "?"), value=r.get("value", ""))
            for r in (data or [])
        ]

    # ------------------------------------------------------------------ peers

    def live_peers(self, symbol: str, quarter: str = "") -> list[NsePeerOut]:
        data = self._call(
            "getPeerComparisonData", QUOTE_TTL,
            symbol=symbol, type="S", quarter=quarter, param="industry", index="",
        )
        return [
            NsePeerOut(
                symbol=r.get("symbol", "?"),
                last_price=_num(r.get("ltp")),
                p_change=_num(r.get("pChange")),
                market_cap=_num(r.get("marketCap")),
                pe=_num(r.get("pe")),
                eps=_num(r.get("eps")),
                net_profit=_num(r.get("pat")),
                total_income=_num(r.get("totalIncome")),
                debt_to_equity=_num(r.get("debtEqRatio")),
                promoter_holding=_num(r.get("promoterHolding")),
                volume=_num(r.get("volume")),
                traded_value=_num(r.get("value")),
            )
            for r in (data or [])
        ]


nse_service = NSEService()
