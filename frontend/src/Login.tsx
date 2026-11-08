import { useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, type Me } from "./api";
import type { Strings } from "./i18n";

export default function Login({ s, controls, onLogin }: { s: Strings; controls: ReactNode; onLogin: (m: Me) => void }) {
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
      setError(err instanceof ApiError ? err.message : "Network error");
      setCode("");
    } finally {
      setPassword("");
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col px-4">
      <div className="flex justify-end py-4">{controls}</div>
      <div className="flex-1 grid place-items-center pb-16">
        <form onSubmit={submit} className="panel w-full max-w-sm p-6 sm:p-8 space-y-4">
          <div className="flex flex-col items-center gap-3 pb-2">
            <div className="orb size-16 rounded-full" />
            <h1 className="text-2xl font-semibold">Pari</h1>
            <p className="muted text-sm">{s.tagline}</p>
          </div>
          <label className="block space-y-1 text-sm">
            <span className="muted">{s.username}</span>
            <input className="field" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="muted">{s.password}</span>
            <input className="field" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="muted">{s.code}</span>
            <input className="field tracking-[0.3em]" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9 ]{6,8}"
              value={code} onChange={(e) => setCode(e.target.value)} required />
          </label>
          {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
          <button disabled={busy} className="w-full rounded-xl py-2.5 font-medium text-white bg-violet-600 hover:bg-violet-500 disabled:opacity-60">
            {busy ? s.signingIn : s.signIn}
          </button>
        </form>
      </div>
    </main>
  );
}
