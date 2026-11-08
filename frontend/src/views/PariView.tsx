import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ApiError, chat, type ChatMessage, type Conversation } from "../api";
import { greeting, type Strings } from "../i18n";
import PariAvatar, { type AvatarState } from "../components/PariAvatar";
import Waveform from "../components/Waveform";
import { IconMic, IconMicOff, IconPlus, IconSend, IconSpeaker, IconSpeakerOff, IconTrash } from "../components/Icons";
import { useMic } from "../lib/useMic";
import { fmtTime } from "../lib/util";

type Bubble = ChatMessage | { id: string; role: "notice"; content: string; created_at: string };

export default function PariView({ s, muted, setMuted, onAuthLost }: {
  s: Strings;
  muted: boolean;
  setMuted: (m: boolean) => void;
  onAuthLost: () => void;
}) {
  const mic = useMic();
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [showList, setShowList] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  const fail = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) onAuthLost();
    else setError(e instanceof ApiError ? e.message : s.networkError);
  }, [onAuthLost, s.networkError]);

  const refreshList = useCallback(() => chat.list().then(setConvs).catch(fail), [fail]);
  useEffect(() => { refreshList(); }, [refreshList]);

  // Messages load only when MK opens a conversation, so a freshly created one
  // doesn't overwrite the bubbles (and the "AI not connected" notice) just added.
  const open = useCallback((id: number | null) => {
    setActive(id);
    setShowList(false);
    if (id === null) setBubbles([]);
    else chat.messages(id).then(setBubbles).catch(fail);
  }, [fail]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [bubbles, sending]);

  async function send(e?: FormEvent) {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    setError("");
    try {
      const id = active ?? (await chat.create()).id;
      if (active === null) setActive(id);
      const r = await chat.send(id, text);
      setDraft("");
      setBubbles((b) => [
        ...b,
        r.message,
        ...(r.reply ? [r.reply] : []),
        ...(r.notice === "ai_not_configured"
          ? [{ id: `n${r.message.id}`, role: "notice" as const, content: s.aiNotice, created_at: r.message.created_at }]
          : []),
      ]);
      refreshList();
    } catch (err) {
      fail(err);
    } finally {
      setSending(false);
    }
  }

  async function remove(id: number) {
    await chat.remove(id).catch(fail);
    if (active === id) open(null);
    refreshList();
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      send();
    }
  }

  const avatarState: AvatarState = sending ? "thinking" : mic.active ? "listening" : "idle";

  return (
    <div className="grid gap-4 lg:h-full lg:min-h-0 lg:grid-cols-[minmax(300px,380px)_1fr]">
      {/* Pari presence card */}
      <section className="panel relative flex flex-col items-center overflow-hidden p-5 text-center lg:p-8">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-[var(--glow)] to-transparent opacity-60" />
        <div className="flex w-full items-center gap-4 lg:flex-col lg:gap-0">
          <PariAvatar state={avatarState} size={88} className="lg:hidden" />
          <PariAvatar state={avatarState} size={210} className="hidden lg:block" />
          <div className="text-left lg:mt-6 lg:text-center">
            <h1 className="font-display text-2xl font-semibold lg:text-3xl">{greeting(s)}</h1>
            <div className="mt-2 flex flex-wrap gap-2 text-xs lg:justify-center">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-1 text-emerald-600 dark:text-emerald-400">
                <span className="size-1.5 rounded-full bg-emerald-500" /> {s.online}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 px-2.5 py-1 text-amber-700 dark:text-amber-300">
                <span className="size-1.5 rounded-full bg-amber-500" /> {s.aiOffline}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-5 w-full lg:mt-8">
          <Waveform analyser={mic.analyser} busy={sending} className="h-12 lg:h-16" />
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button onClick={mic.toggle} aria-pressed={mic.active} aria-label={mic.active ? s.micOn : s.micOff}
            className={`grid size-14 place-items-center rounded-full transition ${mic.active ? "btn-primary" : "btn-ghost"}`}>
            {mic.active ? <IconMic width={24} height={24} /> : <IconMicOff width={24} height={24} />}
          </button>
          <button onClick={() => setMuted(!muted)} aria-pressed={!muted} title={s.voiceLater}
            aria-label={muted ? s.unmute : s.mute} className="btn-ghost grid size-11 place-items-center rounded-full">
            {muted ? <IconSpeakerOff /> : <IconSpeaker />}
          </button>
        </div>
        <p className="muted mt-3 max-w-xs text-xs leading-relaxed">
          {mic.error ? s.micDenied : s.micNote}
        </p>
      </section>

      {/* Chat */}
      <section className="panel flex min-h-[60vh] flex-col overflow-hidden lg:min-h-0">
        <header className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-3">
          <button className="btn-ghost min-w-0 flex-1 truncate rounded-xl px-3 py-2 text-left text-sm" onClick={() => setShowList(!showList)}>
            <span className="muted">{s.conversations}: </span>
            {convs.find((c) => c.id === active)?.title || s.newChat}
          </button>
          <button className="btn-ghost grid size-9 place-items-center rounded-xl" aria-label={s.newChat}
            onClick={() => open(null)}>
            <IconPlus />
          </button>
        </header>

        <div className="relative min-h-0 flex-1">
          {showList && (
            <div className="fade-up absolute inset-0 z-10 overflow-y-auto bg-[var(--panel-solid)] p-2 scroll-thin">
              {convs.length === 0 && <p className="muted p-6 text-center text-sm">{s.noConversations}</p>}
              {convs.map((c) => (
                <div key={c.id} className={`group flex items-center gap-2 rounded-xl px-3 py-2.5 ${c.id === active ? "bg-[var(--glow)]" : "hover:bg-[var(--glow)]"}`}>
                  <button className="min-w-0 flex-1 text-left" onClick={() => open(c.id)}>
                    <div className="truncate text-sm">{c.title || "…"}</div>
                    <div className="muted text-xs">{fmtTime(c.updated_at)}</div>
                  </button>
                  <button className="muted rounded-lg p-1.5 hover:text-red-500" aria-label={s.deleteChat} onClick={() => remove(c.id)}>
                    <IconTrash width={16} height={16} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div ref={scroller} className="scroll-thin absolute inset-0 space-y-3 overflow-y-auto p-4">
            {bubbles.length === 0 && !sending && (
              <div className="grid h-full place-items-center text-center">
                <div className="max-w-sm">
                  <div className="font-display gradient-text text-xl font-semibold">{s.emptyChatTitle}</div>
                  <p className="muted mt-2 text-sm">{s.emptyChatBody}</p>
                </div>
              </div>
            )}
            {bubbles.map((b) => (
              <div key={b.id} className={`fade-up flex ${b.role === "user" ? "justify-end" : "justify-start"}`}>
                {b.role === "notice" ? (
                  <div className="max-w-[85%] rounded-2xl border border-dashed border-amber-500/40 bg-amber-500/10 px-4 py-2.5 text-sm text-amber-800 dark:text-amber-200">
                    {b.content}
                  </div>
                ) : (
                  <div className={`max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed ${
                    b.role === "user" ? "rounded-br-md bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white" : "rounded-bl-md border border-[var(--border)] bg-[var(--panel-solid)]"
                  }`}>
                    {b.content}
                    <div className={`mt-1 text-[11px] ${b.role === "user" ? "text-white/70" : "muted"}`}>{fmtTime(b.created_at)}</div>
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="flex gap-1 px-2 py-3" aria-label="sending">
                {[0, 1, 2].map((i) => <span key={i} className="size-2 animate-bounce rounded-full bg-[var(--accent)]" style={{ animationDelay: `${i * 120}ms` }} />)}
              </div>
            )}
          </div>
        </div>

        <form onSubmit={send} className="border-t border-[var(--border)] p-3">
          {error && <p role="alert" className="mb-2 px-1 text-sm text-red-500">{error}</p>}
          <div className="flex items-end gap-2">
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={onKey} rows={1} maxLength={8000}
              placeholder={s.placeholder} className="field scroll-thin max-h-40 min-h-[46px] resize-none" />
            <button disabled={!draft.trim() || sending} aria-label={s.send}
              className="btn-primary grid size-[46px] shrink-0 place-items-center rounded-xl disabled:opacity-40">
              <IconSend />
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
