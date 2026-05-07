from datetime import date
from typing import Optional, Any
from . import database as db


def get_fund_summary(fund_id: Optional[int] = None) -> list[dict[str, Any]]:
    """Get summary for one fund, or all funds if fund_id is None."""
    funds = db.get_all_funds() if fund_id is None else [db.get_fund(fund_id)]
    funds = [f for f in funds if f is not None]
    if not funds:
        return []

    all_txs = db.get_transactions()
    return [_summarize(f, [t for t in all_txs if t["fund_id"] == f["id"]]) for f in funds]


def _summarize(fund: dict, txs: list[dict]) -> dict:
    buys = [t for t in txs if t["type"] == "buy"]
    sells = [t for t in txs if t["type"] == "sell"]

    total_invested = sum(t["amount"] for t in buys)
    total_returned = sum(t["amount"] for t in sells)
    remaining = round(total_invested - total_returned, 2)

    buy_count = len(buys)
    sell_count = len(sells)

    first_buy = min((t["date"] for t in buys), default=None)
    last_tx = max((t["date"] for t in txs), default=None)

    holding_days = 0
    if first_buy:
        end = date.today().isoformat() if remaining > 0 else (last_tx or first_buy)
        try:
            holding_days = (date.fromisoformat(end) - date.fromisoformat(first_buy)).days
        except (ValueError, TypeError):
            holding_days = 0

    if remaining <= 0 and total_invested > 0:
        total_profit = round(total_returned - total_invested, 2)
        profit_rate = round((total_profit / total_invested) * 100, 2) if total_invested else 0.0
        status = "已清仓"
    elif total_invested > 0:
        total_profit = round(total_returned - total_invested, 2)
        profit_rate = round((total_profit / total_invested) * 100, 2) if total_invested else 0.0
        status = "持有中"
    else:
        total_profit = 0.0
        profit_rate = 0.0
        status = "未投资"

    buy_dates = sorted(set(t["date"] for t in buys))
    sell_dates = sorted(set(t["date"] for t in sells))

    return {
        **fund,
        "total_invested": round(total_invested, 2),
        "total_returned": round(total_returned, 2),
        "remaining": remaining,
        "total_profit": total_profit,
        "profit_rate": profit_rate,
        "holding_days": holding_days,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "buy_dates": buy_dates,
        "sell_dates": sell_dates,
        "first_buy": first_buy,
        "last_tx": last_tx,
        "status": status,
    }


def get_portfolio_summary(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not summaries:
        return {
            "fund_count": 0,
            "active_count": 0,
            "closed_count": 0,
            "total_invested": 0.0,
            "total_returned": 0.0,
            "total_remaining": 0.0,
            "total_profit": 0.0,
            "profit_rate": 0.0,
        }

    total_invested = sum(s["total_invested"] for s in summaries)
    total_returned = sum(s["total_returned"] for s in summaries)
    total_remaining = sum(s["remaining"] for s in summaries)
    total_profit = sum(s["total_profit"] for s in summaries)
    active = sum(1 for s in summaries if s["status"] == "持有中")
    closed = sum(1 for s in summaries if s["status"] == "已清仓")

    return {
        "fund_count": len(summaries),
        "active_count": active,
        "closed_count": closed,
        "total_invested": round(total_invested, 2),
        "total_returned": round(total_returned, 2),
        "total_remaining": round(total_remaining, 2),
        "total_profit": round(total_profit, 2),
        "profit_rate": round((total_profit / total_invested * 100), 2) if total_invested > 0 else 0.0,
    }


def get_transaction_timeline(fund_id: int) -> list[dict[str, Any]]:
    txs = db.get_transactions(fund_id)
    txs.sort(key=lambda t: (t["date"], t["id"]))

    running = 0.0
    for tx in txs:
        if tx["type"] == "buy":
            running += tx["amount"]
        else:
            running -= tx["amount"]
        tx["running_balance"] = round(running, 2)
    return txs
