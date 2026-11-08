import numpy as np
import pandas as pd
import pytest

from mk_pari import backtest, indicators, risk
from mk_pari.agent import PariAgent
from mk_pari.brain import PariView
from mk_pari.brokers import PaperBroker
from mk_pari.config import RiskLimits, Settings


def make_df(n=600, seed=0, drift=0.0005):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.01, n)))
    idx = pd.date_range("2020-01-01", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {"Open": close, "High": close * 1.005, "Low": close * 0.995, "Close": close, "Volume": 1_000},
        index=idx,
    )


def test_rsi_bounds_and_extremes():
    up = pd.Series(np.arange(1, 60, dtype=float))
    assert indicators.rsi(up).iloc[-1] == pytest.approx(100)
    r = indicators.rsi(make_df()["Close"]).dropna()
    assert ((r >= 0) & (r <= 100)).all()


def test_snapshot_keys():
    snap = indicators.snapshot(make_df())
    assert {"last_close", "rsi_14", "sma_200", "atr_14"} <= snap.keys()
    assert snap["sma_200"] is not None


def test_backtest_no_lookahead_and_buy_hold():
    df = make_df()
    always_long = pd.Series(1, index=df.index)
    res = backtest.run(df["Close"], always_long, cost_bps=0)
    # Signal on bar 0 is acted on at bar 0 close, so bar 1 onward is captured.
    expected = df["Close"].iloc[-1] / df["Close"].iloc[0] - 1
    assert res.total_return_pct == pytest.approx(expected * 100, rel=1e-9)
    assert res.trades == 1


def test_risk_sizing_and_rejections():
    lim = RiskLimits(max_risk_per_trade_pct=1, max_position_pct=50, min_reward_risk=1.5)
    ok = risk.evaluate(risk.OrderProposal("X", "buy", 100, 98, 104), 100_000, lim)
    assert ok.approved and ok.quantity == pytest.approx(500)  # 1000 risk / 2 per share

    bad_stop = risk.evaluate(risk.OrderProposal("X", "buy", 100, 101, 104), 100_000, lim)
    assert not bad_stop.approved

    low_rr = risk.evaluate(risk.OrderProposal("X", "sell", 100, 102, 99), 100_000, lim)
    assert not low_rr.approved

    halted = risk.evaluate(risk.OrderProposal("X", "buy", 100, 98, 104), 100_000, lim, realized_pnl_today=-5_000)
    assert not halted.approved


def test_position_cap_binds():
    lim = RiskLimits(max_risk_per_trade_pct=5, max_position_pct=10, min_reward_risk=1)
    d = risk.evaluate(risk.OrderProposal("X", "buy", 100, 99, 102), 100_000, lim)
    assert d.quantity == pytest.approx(100)  # 10% of 100k / 100


class FakeBrain:
    def __init__(self, view):
        self.view = view
        self.calls = []

    def analyse(self, *args, **kw):
        self.calls.append(args)
        return self.view


def _agent(view, **settings):
    return PariAgent(Settings(**settings), brain=FakeBrain(view), broker=PaperBroker(),
                     history_fn=lambda s: make_df(), news_fn=lambda k, t: [])


def test_agent_requires_confirmation():
    view = PariView(action="buy", entry=100, stop_loss=98, take_profit=105, confidence="medium",
                    reasoning="test", reply="ખરીદો")
    a = _agent(view)
    r = a.ask("X", "?")
    assert r.proposal and r.executed is None and not a.broker.orders
    fill = a.confirm(r.proposal.id)
    assert fill["mode"] == "paper" and len(a.broker.orders) == 1
    with pytest.raises(KeyError):
        a.confirm(r.proposal.id)


def test_agent_hold_and_risk_rejection():
    hold = PariView(action="hold", confidence="low", reasoning="", reply="રાહ જુઓ")
    assert _agent(hold).ask("X", "?").proposal is None

    bad = PariView(action="buy", entry=100, stop_loss=99, take_profit=100.5, confidence="high",
                   reasoning="", reply="")
    r = _agent(bad).ask("X", "?")
    assert r.proposal is None and r.risk_reasons


def test_paper_is_never_live():
    assert not Settings(broker="paper", live_trading=True).is_live
    assert not Settings(broker="alpaca", live_trading=False).is_live
