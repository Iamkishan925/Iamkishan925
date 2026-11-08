import { useCallback, useEffect, useState, type ReactNode } from "react";
import { api, type AuditRow, type Health, type Me, type SessionRow, type Status } from "./api";
import type { Strings } from "./i18n";

const STATE_STYLE = {
  ready: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  planned: "bg-slate-500/15 muted",
  disabled: "bg-red-500/15 text-red-600 dark:text-red-400",
} as const;

const fmt = (iso: string) => new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z").toLocaleString();

export default function Dashboard({ s, me, controls, onLogout }: { s: Strings; me: Me; controls: ReactNode; onLogout: () => void }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);

  const refresh = useCallback(() => {
    const onErr = (e: { status?: number }) => e.status === 401 && onLogout();
    api.health().then(setHealth).catch(() => setHealth(null));
    api.status().then(setStatus).catch(onErr);
    api.sessions().then(setSessions).catch(onErr);
    api.audit().then(setAudit).catch(onErr);
  }, [onLogout]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  async function revoke(row: SessionRow) {
    await api.revoke(row.id);
    if (row.current) onLogout();
    else refresh();
  }

  return (
    <main className="mx-auto max-w-6xl px-4 pb-12">
      <header className="flex items-center justify-between py-4 gap-3">
        <div className="flex items-center gap-3">
          <div className="orb size-9 rounded-full" />
          <span className="text-lg font-semibold">Pari</span>
        </div>
        <div className="flex items-center gap-2">
          {controls}
          <button className="panel px-3 py-1.5 text-sm" onClick={() => api.logout().finally(onLogout)}>{s.logout}</button>
        </div>
      </header>

      <section className="panel p-6 sm:p-8 flex flex-col sm:flex-row items-center gap-6">
        <div className="orb size-24 rounded-full shrink-0" />
        <div className="text-center sm:text-left">
          <h1 className="text-2xl sm:text-3xl font-semibold">{s.greeting}</h1>
          <p className="muted mt-2">{s.subtitle}</p>
          <p className="mt-3 inline-block rounded-full px-3 py-1 text-xs bg-red-500/15 text-red-600 dark:text-red-400">
            {status && !status.live_trading ? s.liveOff : "…"}
          </p>
        </div>
      </section>

      <div className="grid gap-4 mt-4 lg:grid-cols-3">
        <section className="panel p-5">
          <h2 className="font-semibold mb-3">{s.system}</h2>
          <dl className="space-y-2 text-sm">
            <Row label={s.backend} value={health ? `${health.status} · v${health.version}` : "offline"} ok={health?.status === "ok"} />
            <Row label={s.database} value={health?.database ?? "?"} ok={health?.database === "ok"} />
            <Row label={me.username} value={me.display_name} ok />
          </dl>
        </section>

        <section className="panel p-5 lg:col-span-2">
          <h2 className="font-semibold mb-3">{s.modules}</h2>
          <ul className="grid sm:grid-cols-2 gap-2 text-sm">
            {status?.modules.map((m) => (
              <li key={m.name} className="flex items-start justify-between gap-2 rounded-xl border border-[var(--border)] px-3 py-2">
                <div className="min-w-0">
                  <div className="font-medium">{m.name}</div>
                  <div className="muted text-xs">{m.note}</div>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${STATE_STYLE[m.state]}`}>{s[m.state]}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel p-5">
          <h2 className="font-semibold mb-3">{s.sessions}</h2>
          <ul className="space-y-2 text-sm">
            {sessions.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate">{r.user_agent || "unknown"}</div>
                  <div className="muted text-xs">{r.ip} · {fmt(r.last_seen)} {r.current && `· ${s.thisDevice}`}</div>
                </div>
                <button className="text-xs text-red-500 shrink-0" onClick={() => revoke(r)}>{s.revoke}</button>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel p-5 lg:col-span-2">
          <h2 className="font-semibold mb-3">{s.activity}</h2>
          <ul className="text-sm divide-y divide-[var(--border)]">
            {audit.map((e, i) => (
              <li key={i} className="py-2 flex flex-wrap gap-x-3">
                <span className="muted text-xs w-40 shrink-0">{fmt(e.ts)}</span>
                <span className="font-medium">{e.action}</span>
                <span className="muted text-xs">{e.actor} · {e.ip}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="muted">{label}</dt>
      <dd className="flex items-center gap-2">
        <span className={`size-2 rounded-full ${ok ? "bg-emerald-500" : "bg-red-500"}`} />
        {value}
      </dd>
    </div>
  );
}
