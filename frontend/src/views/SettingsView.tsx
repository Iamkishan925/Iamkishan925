import type { ReactNode } from "react";
import type { Lang, Strings } from "../i18n";

export type Theme = "dark" | "light";

export default function SettingsView(props: {
  s: Strings;
  theme: Theme;
  setTheme: (t: Theme) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  muted: boolean;
  setMuted: (m: boolean) => void;
  replayIntro: () => void;
}) {
  const { s } = props;
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <section className="panel divide-y divide-[var(--border)]">
        <Setting label={s.theme}>
          <Segmented value={props.theme} onChange={props.setTheme} options={[["dark", s.dark], ["light", s.light]]} />
        </Setting>
        <Setting label={s.language}>
          <Segmented value={props.lang} onChange={props.setLang} options={[["gu", "ગુજરાતી"], ["en", "English"]]} />
        </Setting>
        <Setting label={s.voice} hint={s.voiceLater}>
          <Segmented value={props.muted ? "off" : "on"} onChange={(v) => props.setMuted(v === "off")}
            options={[["on", s.unmute], ["off", s.mute]]} />
        </Setting>
      </section>
      <button className="btn-ghost w-full rounded-xl px-4 py-3 text-sm" onClick={props.replayIntro}>{s.replayIntro}</button>
    </div>
  );
}

function Setting({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="font-medium">{label}</div>
        {hint && <div className="muted text-xs">{hint}</div>}
      </div>
      {children}
    </div>
  );
}

function Segmented<T extends string>({ value, onChange, options }: { value: T; onChange: (v: T) => void; options: [T, string][] }) {
  return (
    <div className="inline-flex rounded-xl border border-[var(--border)] p-1" role="radiogroup">
      {options.map(([v, label]) => (
        <button key={v} role="radio" aria-checked={value === v} onClick={() => onChange(v)}
          className={`rounded-lg px-3 py-1.5 text-sm transition ${value === v ? "btn-primary" : "muted hover:text-[var(--text)]"}`}>
          {label}
        </button>
      ))}
    </div>
  );
}
