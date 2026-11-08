import { useEffect, useRef, useState } from "react";
import { api, type AuditRow } from "../api";
import type { Strings } from "../i18n";
import { fmtTime, loadPref, savePref, toDate } from "../lib/util";
import { IconBell } from "./Icons";

// Live security notifications, built from the real audit log (polled every 20s).
// Market/news alerts join this list in Phase 5.
const LABELS: Record<string, { gu: string; en: string; tone: "warn" | "info" }> = {
  login_failed: { gu: "ખોટો login પ્રયાસ", en: "Failed sign-in attempt", tone: "warn" },
  login_blocked: { gu: "Login lock થયું (ઘણા ખોટા પ્રયાસ)", en: "Sign-in locked (too many failures)", tone: "warn" },
  login: { gu: "નવું login", en: "New sign-in", tone: "info" },
  session_revoked: { gu: "Device sign out થયું", en: "Device signed out", tone: "info" },
  totp_reset: { gu: "Authenticator બદલાયું", en: "Authenticator reset", tone: "warn" },
};

export default function Notifications({ s, lang }: { s: Strings; lang: "gu" | "en" }) {
  const [items, setItems] = useState<AuditRow[]>([]);
  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState<string>(() => loadPref<string>("pari.notif.seen", ""));
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = () => api.audit().then((rows) => setItems(rows.filter((r) => r.action in LABELS))).catch(() => {});
    load();
    const id = setInterval(load, 20_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const seenAt = seen ? toDate(seen).getTime() : 0;
  const unread = items.filter((i) => toDate(i.ts).getTime() > seenAt).length;

  function markRead() {
    const latest = items[0]?.ts ?? new Date().toISOString();
    setSeen(latest);
    savePref("pari.notif.seen", latest);
  }

  return (
    <div className="relative" ref={box}>
      <button className="btn-ghost relative grid size-10 place-items-center rounded-xl" aria-label={s.notifications}
        onClick={() => setOpen(!open)}>
        <IconBell />
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 grid min-w-5 place-items-center rounded-full bg-pink-500 px-1 text-[11px] font-semibold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="panel fade-up absolute right-0 top-12 z-40 w-[min(22rem,calc(100vw-2rem))] overflow-hidden !bg-[var(--panel-solid)] shadow-2xl">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <span className="font-medium">{s.notifications}</span>
            <button className="text-xs text-[var(--accent)]" onClick={markRead}>{s.markRead}</button>
          </div>
          <ul className="scroll-thin max-h-80 overflow-y-auto">
            {items.length === 0 && <li className="muted px-4 py-6 text-center text-sm">{s.noNotifications}</li>}
            {items.map((i, n) => {
              const meta = LABELS[i.action];
              const isNew = toDate(i.ts).getTime() > seenAt;
              return (
                <li key={n} className="flex gap-3 border-b border-[var(--border)] px-4 py-3 last:border-0">
                  <span className={`mt-1.5 size-2 shrink-0 rounded-full ${meta.tone === "warn" ? "bg-amber-400" : "bg-cyan-400"} ${isNew ? "" : "opacity-30"}`} />
                  <div className="min-w-0 text-sm">
                    <div className={isNew ? "font-medium" : ""}>{meta[lang]}</div>
                    <div className="muted text-xs">{fmtTime(i.ts)} · {i.ip}</div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
