# Pari architecture

## Principles

1. **The LLM proposes, code decides.** Every number that matters is computed by deterministic,
   tested code: indicators, position size, risk/reward, limits. Claude explains and suggests.
2. **The risk engine is separate from AI and execution.** No AI output reaches a broker without
   passing it.
3. **Real money is off by default.** Live trading needs three independent switches: a server
   environment flag, arming from the dashboard with MFA, and per-order approval. A kill switch
   always works.
4. **Honest status.** A module is marked `ready` only when it really works.
5. **Least privilege.** Every integration has explicit scopes and can be disabled or disconnected.

## System

```
 Phone (PWA) / Laptop ──HTTPS/WSS──► Caddy (TLS, headers, static PWA)
                                        │ internal network only
                                        ▼
                                FastAPI backend
   auth · audit · ai(Claude) · voice · memory · integrations · notifications
   market_data · news · analysis · strategies · backtest · paper · risk · execution
                                        │
                     PostgreSQL ─ users, sessions, memory, orders, audit
                     Parquet + DuckDB ─ historical candles (Phase 7)
```

For remote access, either use a public domain behind Caddy with TLS and MFA, or keep Pari
private on a Tailscale tailnet or behind Cloudflare Tunnel + Access. Never open the backend or
database ports.

## Planned module boundaries (backend/pari/)

| Module | Phase | Responsibility |
|---|---|---|
| `auth`, `audit` | 1 ✅ | login, MFA, sessions, lockout, activity log |
| `api/chat` | 2 ✅ | conversation storage; `app.state.assistant` hook for the AI |
| `ai` | 3 | Claude client, model from config, tool registry with per-tool permission |
| `voice` | 3 | `SpeechToText` / `TextToSpeech` provider interfaces (Google, Azure, ElevenLabs) |
| `memory` | 4 | user-approved memories, encrypted, view/edit/delete |
| `integrations` | 4 | connector registry: scopes, enable/disable/disconnect |
| `market_data` | 5 | broker/data adapters (OANDA first), bid/ask, spread, stale-price checks |
| `news` | 5 | news + economic calendar providers, source/time/confidence on every item |
| `analysis` | 6 | indicators, patterns, structure, multi-timeframe |
| `strategies` | 6 | plugin interface: each strategy can be enabled, tested and compared on its own |
| `backtest` | 7 | costs, slippage, walk-forward, out-of-sample |
| `paper`, `risk` | 8 | simulated account; max risk/trade, daily loss, positions, exposure, spread, slippage, duplicates, kill switch |
| `execution` | 9 | demo-account orders with human approval; live only after Phase 11 sign-off |
| `notifications` | 10 | Web Push, Telegram |

## Phases

1. Scaffold, auth, dashboard shell, CI, Docker ✅
2. Premium dashboard, original animated Pari avatar, chat UI ✅
3. Claude conversations (gu/hi/en and mixed), STT/TTS with a female voice
4. Memory and the integrations framework
5. Forex data, live charts, news and calendar
6. Technical analysis and strategy engine
7. Historical datasets and backtesting
8. Paper trading and risk management
9. Broker integration (demo) with human approval
10. Production deployment, PWA install, notifications, monitoring, backups
11. Limited live trading, only after separate explicit authorization and successful testing
