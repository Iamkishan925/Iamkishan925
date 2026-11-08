import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type AuditRow, type Health, type Me, type SessionRow, type Status } from "../api";
import type { Strings } from "../i18n";
import { fmtTime } from "../lib/util";

const STATE_STYLE = {
  ready: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  planned: "bg-slate-500/15 muted",
  disabled: "bg-red-500/15 text-red-600 dark:text-red-400",
} as const;

export default function SystemView({ s, me, onAuthLost }: { s: Strings; me: Me; onAuthLost: () => void }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);

  const refresh = useCallback(() => {
    const onErr = (e: unknown) => e instanceof ApiError && e.status === 401 && onAuthLost();
    api.health().then(setHealth).catch(() => setHealth(null));
    api.status().then(setStatus).catch(onErr);
    api.sessions().then(setSessions).catch(onErr);
    api.audit().then(setAudit).catch(onErr);
  }, [onAuthLost]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  async function revoke(row: SessionRow) {
    await api.revoke(row.id);
    if (row.current) onAuthLost();
    else refresh();
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <section className="panel p-5">
        <h2 className="font-display mb-4 font-semibold">{s.system}</h2>
        <dl className="space-y-3 text-sm">
          <Row label={s.backend} value={health ? `${health.status} · v${health.version}` : "offline"} ok={health?.status === "ok"} />
          <Row label={s.database} value={health?.database ?? "?"} ok={health?.database === "ok"} />
          <Row label="Owner" value={`${me.display_name} (${me.username})`} ok />
          <Row label="Live trading" value={s.disabled} ok={false} />
        </dl>
      </section>

      <section className="panel p-5 lg:col-span-2">
        <h2 className="font-display mb-4 font-semibold">{s.modules}</h2>
        <ul className="grid gap-2 text-sm sm:grid-cols-2">
          {status?.modules.map((m) => (
            <li key={m.name} className="panel-hover flex items-start justify-between gap-2 rounded-xl border border-[var(--border)] px-3 py-2.5">
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
        <h2 className="font-display mb-4 font-semibold">{s.sessions}</h2>
        <ul className="space-y-3 text-sm">
          {sessions.map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate">{r.user_agent || "unknown"}</div>
                <div className="muted text-xs">{r.ip} · {fmtTime(r.last_seen)} {r.current && `· ${s.thisDevice}`}</div>
              </div>
              <button className="shrink-0 text-xs text-red-500" onClick={() => revoke(r)}>{s.revoke}</button>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel p-5 lg:col-span-2">
        <h2 className="font-display mb-4 font-semibold">{s.activity}</h2>
        <ul className="divide-y divide-[var(--border)] text-sm">
          {audit.map((e, i) => (
            <li key={i} className="flex flex-wrap gap-x-3 py-2">
              <span className="muted w-32 shrink-0 text-xs">{fmtTime(e.ts)}</span>
              <span className="font-medium">{e.action}</span>
              <span className="muted text-xs">{e.actor} · {e.ip}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="muted">{label}</dt>
      <dd className="flex items-center gap-2 text-right">
        <span className={`size-2 rounded-full ${ok ? "bg-emerald-500" : "bg-red-500"}`} />
        {value}
      </dd>
    </div>
  );
}
