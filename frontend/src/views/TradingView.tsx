import type { Strings } from "../i18n";
import { IconChart, IconLock } from "../components/Icons";

// Honest placeholder: no fake prices or charts until a real data feed is connected (Phase 5).
const ROADMAP = [
  { phase: 5, gu: "Live forex ભાવ, bid/ask, spread, charts, news, economic calendar", en: "Live forex prices, bid/ask, spread, charts, news, economic calendar" },
  { phase: 6, gu: "Technical analysis (RSI, MACD, ATR, structure…) અને strategy engine", en: "Technical analysis (RSI, MACD, ATR, structure…) and strategy engine" },
  { phase: 7, gu: "15 વર્ષ સુધીના licensed historical data પર backtesting", en: "Backtesting on up to 15 years of licensed historical data" },
  { phase: 8, gu: "Paper trading અને independent risk engine", en: "Paper trading and an independent risk engine" },
  { phase: 9, gu: "Demo account પર તમારી approval સાથે orders", en: "Demo-account orders with your approval" },
];

export default function TradingView({ s, lang }: { s: Strings; lang: "gu" | "en" }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <section className="panel relative overflow-hidden p-6 lg:col-span-2 lg:p-8">
        <div className="grid-overlay" />
        <div className="relative">
          <div className="grid size-12 place-items-center rounded-2xl bg-[var(--glow)] text-[var(--accent)]"><IconChart width={26} height={26} /></div>
          <h1 className="font-display mt-4 text-2xl font-semibold">{s.tradingTitle}</h1>
          <p className="muted mt-2 max-w-xl">{s.tradingBody}</p>
          <ol className="mt-6 space-y-3">
            {ROADMAP.map((r) => (
              <li key={r.phase} className="flex gap-3">
                <span className="font-display grid size-8 shrink-0 place-items-center rounded-lg border border-[var(--border)] text-sm">{r.phase}</span>
                <span className="pt-1 text-sm">{r[lang]}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>
      <section className="panel p-6">
        <div className="grid size-12 place-items-center rounded-2xl bg-red-500/15 text-red-500"><IconLock width={24} height={24} /></div>
        <h2 className="font-display mt-4 text-lg font-semibold">{s.liveOff}</h2>
        <p className="muted mt-2 text-sm">{s.tradingSafety}</p>
      </section>
    </div>
  );
}
