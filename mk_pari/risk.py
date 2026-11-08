"""Hard risk rules. Claude proposes; this module decides whether an order is allowed.

Nothing Claude says can bypass these checks - they run in plain code after
the model's proposal and before any broker call.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import RiskLimits


@dataclass
class OrderProposal:
    symbol: str
    side: str  # buy | sell
    entry: float
    stop_loss: float
    take_profit: float
    rationale: str = ""


@dataclass
class RiskDecision:
    approved: bool
    quantity: float
    reasons: list[str]


def atr_levels(entry: float, atr: float, side: str, stop_mult: float = 1.5, rr: float = 2.0):
    """Stop-loss / take-profit from ATR. Returns (stop, target)."""
    d = atr * stop_mult
    if side == "buy":
        return entry - d, entry + d * rr
    return entry + d, entry - d * rr


def evaluate(
    p: OrderProposal,
    equity: float,
    limits: RiskLimits,
    realized_pnl_today: float = 0.0,
) -> RiskDecision:
    reasons: list[str] = []
    if p.side not in {"buy", "sell"}:
        return RiskDecision(False, 0, [f"unknown side {p.side!r}"])
    if min(p.entry, p.stop_loss, p.take_profit) <= 0 or equity <= 0:
        return RiskDecision(False, 0, ["prices and equity must be positive"])

    long = p.side == "buy"
    stop_dist = p.entry - p.stop_loss if long else p.stop_loss - p.entry
    reward = p.take_profit - p.entry if long else p.entry - p.take_profit
    if stop_dist <= 0:
        reasons.append("stop-loss is on the wrong side of entry")
    if reward <= 0:
        reasons.append("take-profit is on the wrong side of entry")
    if stop_dist > 0 and reward > 0 and reward / stop_dist < limits.min_reward_risk:
        reasons.append(f"reward/risk {reward / stop_dist:.2f} below minimum {limits.min_reward_risk}")
    if realized_pnl_today <= -equity * limits.max_daily_loss_pct / 100:
        reasons.append("daily loss limit reached - trading halted for today")
    if reasons:
        return RiskDecision(False, 0, reasons)

    qty_by_risk = equity * limits.max_risk_per_trade_pct / 100 / stop_dist
    qty_by_size = equity * limits.max_position_pct / 100 / p.entry
    qty = min(qty_by_risk, qty_by_size)
    if qty <= 0:
        return RiskDecision(False, 0, ["computed quantity is zero"])
    binding = "risk limit" if qty_by_risk <= qty_by_size else "position-size cap"
    return RiskDecision(True, qty, [f"quantity set by {binding}"])
