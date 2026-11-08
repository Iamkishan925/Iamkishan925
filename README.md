# MK-Pari: a trading assistant built on Claude

Pari is a trading assistant that speaks Gujarati, Hindi and English. For any stock or forex symbol it
pulls price history, works out technical indicators, runs a 15-year backtest and reads recent news.
Claude then gives a view with entry, stop-loss and take-profit levels. Plain-code risk rules check
that view, and **you** confirm before any order goes out. It runs on **paper trading by default**.

```
yfinance history ─┐
indicators (RSI, MACD, BB, ATR, SMA) ─┼─► Claude (Pari) ─► risk engine ─► your "yes" ─► broker
15y SMA50/200 backtest ─┤                  structured view     hard limits     (CLI / web)     paper | Alpaca
Alpha Vantage news + sentiment ─┘                                                    
                                       reply text ─► ElevenLabs TTS (Pari's voice)
```

## Safety model

- **Claude only proposes trades.** `mk_pari/risk.py` checks every proposal in plain code. It sizes
  the position from your risk %, caps the notional, rejects a stop or target on the wrong side of
  entry, enforces a minimum reward/risk, and halts trading after the daily loss limit.
- **You confirm every order.** A proposal waits for your yes and expires after 5 minutes.
  `AUTO_EXECUTE=true` turns this off; don't use it until you've tested the bot for a long time.
- **Live trading takes two switches:** `LIVE_TRADING=true` *and* a real broker (`BROKER=alpaca`).
  The `paper` broker can never trade live.
- Secrets live only in environment variables (`.env.example`). The web API needs a bearer token.
- A backtest is not a forecast, and an LLM's market view can be wrong. Start small.

## Setup

```bash
pip install -e ".[dev]"
```

```bash
cp .env.example .env   # fill ANTHROPIC_API_KEY at minimum, then export the vars
```

```bash
pytest -q
```

## Use

```bash
python -m mk_pari.cli --backtest AAPL
```

```bash
python -m mk_pari.cli EURUSD=X "aaje EURUSD ma trade che?" --lang gu --news FOREX:EUR FOREX:USD
```

Web API (phone/laptop):

```bash
uvicorn mk_pari.app:app --host 0.0.0.0 --port 8000
```

| Endpoint | What it does |
|---|---|
| `GET /health` | mode (paper/LIVE) and broker |
| `POST /ask` `{symbol, question, news_tickers?, language?}` | Pari's view, risk result, and a `proposal_id` if a trade passed the risk checks |
| `POST /confirm/{id}` / `POST /reject/{id}` | place or drop the proposed bracket order |
| `POST /speak` `{text}` | MP3 of Pari speaking the text (ElevenLabs) |

All endpoints except `/health` need `Authorization: Bearer $PARI_API_TOKEN`.

## Deploy (e.g. a UK server such as AWS London)

```bash
docker build -t mk-pari .
```

```bash
docker run -d --env-file .env -p 127.0.0.1:8000:8000 mk-pari
```

Put HTTPS in front of it (Caddy or nginx with Let's Encrypt, or a cloud load balancer). Don't expose
port 8000 to the internet directly.

## Layout

| File | Role |
|---|---|
| `mk_pari/config.py` | env-based settings and risk limits |
| `mk_pari/data.py` | yfinance history (`AAPL`, `RELIANCE.NS`, `EURUSD=X`, `GC=F`) |
| `mk_pari/indicators.py` | SMA/EMA/RSI/MACD/Bollinger/ATR in pandas |
| `mk_pari/backtest.py` | vectorised backtester (no look-ahead, trading costs, Sharpe, drawdown) |
| `mk_pari/news.py` | Alpha Vantage NEWS_SENTIMENT |
| `mk_pari/brain.py` | Claude call: Pari system prompt, structured `PariView` output |
| `mk_pari/risk.py` | hard risk rules and position sizing |
| `mk_pari/brokers/` | `Broker` interface, `PaperBroker`, `AlpacaBroker` |
| `mk_pari/agent.py` | runs the full flow and holds proposals until you confirm |
| `mk_pari/app.py`, `mk_pari/cli.py` | web API and terminal chat |

## Next steps

- Forex execution: add `brokers/mt5.py` (MetaTrader5) or `brokers/ibkr.py` (`ib_insync`) that
  implements `Broker`.
- Track realized P&L from broker fills so the daily loss limit uses real numbers. Today
  `realized_pnl_today` is never updated.
- Keep pending proposals and the trade log in a database (they're in memory now).
- Add a small web or Telegram front end that calls `/ask`, shows a chart (Plotly) and plays `/speak`.
