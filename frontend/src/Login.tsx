import { useState, type FormEvent } from "react";
import { api, ApiError, type Me } from "./api";
import type { Lang, Strings } from "./i18n";
import PariAvatar from "./components/PariAvatar";

export default function Login({ s, lang, setLang, onLogin }: {
  s: Strings;
  lang: Lang;
  setLang: (l: Lang) => void;
  onLogin: (m: Me) => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api.login(username, password, code));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : s.networkError);
      setCode("");
    } finally {
      setPassword("");
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-full flex-col px-4">
      <div className="flex justify-end py-4">
        <button className="btn-ghost rounded-xl px-3 py-1.5 text-sm" onClick={() => setLang(lang === "gu" ? "en" : "gu")}>
          {lang === "gu" ? "English" : "ગુજરાતી"}
        </button>
      </div>
      <div className="grid flex-1 place-items-center pb-16">
        <form onSubmit={submit} className="panel fade-up w-full max-w-sm space-y-4 p-6 sm:p-8">
          <div className="flex flex-col items-center gap-3 pb-2">
            <PariAvatar size={112} state={busy ? "thinking" : "idle"} />
            <h1 className="font-display gradient-text mt-2 text-3xl font-semibold tracking-[0.2em]">PARI</h1>
            <p className="muted text-sm">{s.tagline}</p>
          </div>
          <label className="block space-y-1.5 text-sm">
            <span className="muted">{s.username}</span>
            <input className="field" autoComplete="username" autoCapitalize="none" value={username}
              onChange={(e) => setUsername(e.target.value)} required />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="muted">{s.password}</span>
            <input className="field" type="password" autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="muted">{s.code}</span>
            <input className="field text-center tracking-[0.4em]" inputMode="numeric" autoComplete="one-time-code"
              pattern="[0-9 ]{6,8}" maxLength={8} value={code} onChange={(e) => setCode(e.target.value)} required />
          </label>
          {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
          <button type="submit" disabled={busy} className="btn-primary w-full rounded-xl py-3 font-medium disabled:opacity-60">
            {busy ? s.signingIn : s.signIn}
          </button>
        </form>
      </div>
    </main>
  );
}
