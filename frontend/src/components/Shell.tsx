import type { ComponentType, ReactNode, SVGProps } from "react";
import type { Strings } from "../i18n";
import PariAvatar from "./PariAvatar";
import { IconChart, IconLogout, IconMoon, IconSettings, IconShield, IconSpark, IconSun } from "./Icons";

export type View = "pari" | "trading" | "system" | "settings";

const NAV: { id: View; key: keyof Strings; icon: ComponentType<SVGProps<SVGSVGElement>> }[] = [
  { id: "pari", key: "navPari", icon: IconSpark },
  { id: "trading", key: "navTrading", icon: IconChart },
  { id: "system", key: "navSystem", icon: IconShield },
  { id: "settings", key: "navSettings", icon: IconSettings },
];

export default function Shell({ s, view, setView, theme, toggleTheme, onLogout, bell, children }: {
  s: Strings;
  view: View;
  setView: (v: View) => void;
  theme: "dark" | "light";
  toggleTheme: () => void;
  onLogout: () => void;
  bell: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex h-full">
      {/* desktop sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-[var(--border)] p-4 lg:flex">
        <div className="flex items-center gap-3 px-2 py-2">
          <PariAvatar size={36} />
          <span className="font-display text-lg font-semibold tracking-wide">PARI</span>
        </div>
        <nav className="mt-6 space-y-1">
          {NAV.map(({ id, key, icon: Icon }) => (
            <button key={id} onClick={() => setView(id)} aria-current={view === id ? "page" : undefined}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                view === id ? "bg-[var(--glow)] font-medium text-[var(--text)]" : "muted hover:bg-[var(--glow)] hover:text-[var(--text)]"
              }`}>
              <Icon /> {s[key]}
            </button>
          ))}
        </nav>
        <div className="mt-auto">
          <button onClick={onLogout} className="muted flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm hover:text-[var(--text)]">
            <IconLogout /> {s.logout}
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 px-4 py-3 lg:px-8 lg:py-5">
          <div className="flex items-center gap-2 lg:hidden">
            <PariAvatar size={32} />
            <span className="font-display font-semibold tracking-wide">PARI</span>
          </div>
          <div className="font-display hidden text-xl font-semibold lg:block">{s[NAV.find((n) => n.id === view)!.key]}</div>
          <div className="flex items-center gap-2">
            {bell}
            <button className="btn-ghost grid size-10 place-items-center rounded-xl" aria-label="Toggle theme" onClick={toggleTheme}>
              {theme === "dark" ? <IconSun /> : <IconMoon />}
            </button>
            <button className="btn-ghost grid size-10 place-items-center rounded-xl lg:hidden" aria-label={s.logout} onClick={onLogout}>
              <IconLogout />
            </button>
          </div>
        </header>

        <main key={view} className="fade-up min-h-0 flex-1 overflow-y-auto px-4 pb-24 lg:px-8 lg:pb-8">{children}</main>

        {/* mobile bottom nav */}
        <nav className="panel fixed inset-x-3 bottom-3 z-30 grid grid-cols-4 !rounded-2xl p-1.5 lg:hidden"
          style={{ paddingBottom: "max(0.375rem, env(safe-area-inset-bottom))" }}>
          {NAV.map(({ id, key, icon: Icon }) => (
            <button key={id} onClick={() => setView(id)} aria-current={view === id ? "page" : undefined}
              className={`flex flex-col items-center gap-0.5 rounded-xl py-2 text-[11px] transition ${
                view === id ? "bg-[var(--glow)] text-[var(--text)]" : "muted"
              }`}>
              <Icon width={22} height={22} /> {s[key]}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
