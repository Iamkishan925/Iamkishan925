import { useEffect, useState } from "react";
import { api, type Me } from "./api";
import { t, type Lang } from "./i18n";
import Login from "./Login";
import Dashboard from "./Dashboard";

type Theme = "dark" | "light";

function load<T extends string>(key: string, fallback: T): T {
  try {
    return (localStorage.getItem(key) as T) || fallback;
  } catch {
    return fallback;
  }
}
function save(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode: preference just isn't remembered */
  }
}

export default function App() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [theme, setTheme] = useState<Theme>(() => load("pari.theme", "dark"));
  const [lang, setLang] = useState<Lang>(() => load("pari.lang", "gu"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    save("pari.theme", theme);
  }, [theme]);
  useEffect(() => {
    document.documentElement.lang = lang;
    save("pari.lang", lang);
  }, [lang]);

  useEffect(() => {
    // Any failure (401, or backend down) shows the login screen.
    api.me().then(setMe).catch(() => setMe(null));
  }, []);

  const s = t(lang);
  const controls = (
    <div className="flex items-center gap-2 text-sm">
      <button className="panel px-3 py-1.5" onClick={() => setLang(lang === "gu" ? "en" : "gu")}>
        {lang === "gu" ? "English" : "ગુજરાતી"}
      </button>
      <button className="panel px-3 py-1.5" aria-label="Toggle theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
        {theme === "dark" ? "☀" : "☾"}
      </button>
    </div>
  );

  if (me === undefined) return <div className="min-h-screen grid place-items-center"><div className="orb size-16 rounded-full" /></div>;
  if (me === null) return <Login s={s} controls={controls} onLogin={setMe} />;
  return <Dashboard s={s} me={me} controls={controls} onLogout={() => setMe(null)} />;
}
