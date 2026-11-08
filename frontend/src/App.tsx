import { useCallback, useEffect, useState } from "react";
import { api, type Me } from "./api";
import { t, type Lang } from "./i18n";
import { loadPref, savePref } from "./lib/util";
import Login from "./Login";
import Intro from "./components/Intro";
import Shell, { type View } from "./components/Shell";
import Notifications from "./components/Notifications";
import PariAvatar from "./components/PariAvatar";
import PariView from "./views/PariView";
import TradingView from "./views/TradingView";
import SystemView from "./views/SystemView";
import SettingsView, { type Theme } from "./views/SettingsView";

const VIEWS: View[] = ["pari", "trading", "system", "settings"];
const viewFromHash = (): View => {
  const h = location.hash.slice(1) as View;
  return VIEWS.includes(h) ? h : "pari";
};

function introSeen(): boolean {
  try {
    return sessionStorage.getItem("pari.intro") === "1";
  } catch {
    return false;
  }
}

export default function App() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [theme, setTheme] = useState<Theme>(() => loadPref("pari.theme", "dark"));
  const [lang, setLang] = useState<Lang>(() => loadPref("pari.lang", "gu"));
  const [muted, setMuted] = useState(() => loadPref<string>("pari.muted", "0") === "1");
  const [view, setViewState] = useState<View>(viewFromHash);
  const [intro, setIntro] = useState(() => !introSeen());

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "dark" ? "#07060f" : "#f4f2fb");
    savePref("pari.theme", theme);
  }, [theme]);
  useEffect(() => {
    document.documentElement.lang = lang;
    savePref("pari.lang", lang);
  }, [lang]);
  useEffect(() => savePref("pari.muted", muted ? "1" : "0"), [muted]);

  useEffect(() => {
    const onHash = () => setViewState(viewFromHash());
    addEventListener("hashchange", onHash);
    return () => removeEventListener("hashchange", onHash);
  }, []);
  const setView = (v: View) => {
    location.hash = v;
    setViewState(v);
  };

  useEffect(() => {
    api.me().then(setMe).catch(() => setMe(null)); // 401 or backend down -> login screen
  }, []);

  const endIntro = useCallback(() => {
    setIntro(false);
    try {
      sessionStorage.setItem("pari.intro", "1");
    } catch {
      /* ignore */
    }
  }, []);
  const authLost = useCallback(() => setMe(null), []);

  const s = t(lang);

  return (
    <>
      <div className="aurora"><div className="grid-overlay" /></div>
      {intro && <Intro onDone={endIntro} skipLabel={s.skip} />}
      {me === undefined ? (
        <div className="grid h-full place-items-center"><PariAvatar size={96} state="thinking" /></div>
      ) : me === null ? (
        <Login s={s} lang={lang} setLang={setLang} onLogin={setMe} />
      ) : (
        <Shell s={s} view={view} setView={setView} theme={theme}
          toggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
          onLogout={() => api.logout().finally(authLost)}
          bell={<Notifications s={s} lang={lang} />}>
          {view === "pari" && <PariView s={s} muted={muted} setMuted={setMuted} onAuthLost={authLost} />}
          {view === "trading" && <TradingView s={s} lang={lang} />}
          {view === "system" && <SystemView s={s} me={me} onAuthLost={authLost} />}
          {view === "settings" && (
            <SettingsView s={s} theme={theme} setTheme={setTheme} lang={lang} setLang={setLang}
              muted={muted} setMuted={setMuted} replayIntro={() => setIntro(true)} />
          )}
        </Shell>
      )}
    </>
  );
}
