// UI strings. Gujarati is the default; English is available from the header.
// Hindi is added with the language work in Phase 3.

export type Lang = "gu" | "en";

const strings = {
  gu: {
    tagline: "MK નું પર્સનલ AI",
    signIn: "Sign in",
    username: "Username",
    password: "Password",
    code: "Authenticator code",
    signingIn: "ચકાસી રહી છું…",
    greeting: "નમસ્તે MK",
    subtitle: "Phase 1: સુરક્ષિત પાયો તૈયાર છે. બાકીના modules એક પછી એક ઉમેરાશે.",
    system: "System status",
    modules: "Modules",
    sessions: "Signed-in devices",
    activity: "Activity log",
    revoke: "Sign out",
    thisDevice: "આ device",
    logout: "Logout",
    liveOff: "Live trading બંધ છે",
    ready: "તૈયાર",
    planned: "આયોજિત",
    disabled: "બંધ",
    backend: "Backend",
    database: "Database",
  },
  en: {
    tagline: "MK's personal AI",
    signIn: "Sign in",
    username: "Username",
    password: "Password",
    code: "Authenticator code",
    signingIn: "Checking…",
    greeting: "Hello MK",
    subtitle: "Phase 1: the secure foundation is in place. Other modules arrive one by one.",
    system: "System status",
    modules: "Modules",
    sessions: "Signed-in devices",
    activity: "Activity log",
    revoke: "Sign out",
    thisDevice: "this device",
    logout: "Logout",
    liveOff: "Live trading is off",
    ready: "ready",
    planned: "planned",
    disabled: "disabled",
    backend: "Backend",
    database: "Database",
  },
} as const;

export type Strings = { [K in keyof (typeof strings)["gu"]]: string };
export const t = (lang: Lang): Strings => strings[lang];
