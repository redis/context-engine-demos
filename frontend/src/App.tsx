import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatRole = "user" | "assistant";

type ToolEvent = {
  toolName: string;
  toolKind: "internal_function" | "mcp_tool";
  status: "call" | "result";
  payload: Record<string, unknown>;
  durationMs?: number;
  ts?: number;
};

type MergedToolEvent = {
  toolName: string;
  toolKind: ToolEvent["toolKind"];
  callPayload?: Record<string, unknown>;
  resultPayload?: Record<string, unknown>;
  durationMs?: number;
  ts?: number;
};

type ThinkingStep = {
  id: string;
  text: string;
  ts: number;
  kind: "plan" | "llm";
  durationMs?: number;
  durationText?: string;
};

type StatusMessage = { text: string; ts: number };

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  statusMessages: StatusMessage[];
  thinkingSteps: ThinkingStep[];
  toolEvents: ToolEvent[];
  totalElapsedMs?: number;
};

type HealthState = {
  ok: boolean;
  domain: string;
  mcp_enabled: boolean;
  internal_tools: string[];
} | null;

type AgentMode = "context_surfaces" | "simple_rag";

type PromptCard = { eyebrow: string; title: string; prompt: string };

type DomainConfig = {
  id: string;
  app_name: string;
  subtitle: string;
  hero_title: string;
  placeholder_text: string;
  starter_prompts: PromptCard[];
  theme: Record<string, string>;
  logo_src: string;
} | null;

const modeStorageKey = "demo-domain-mode";

function toolKindLabel(kind: ToolEvent["toolKind"]) {
  return kind === "mcp_tool" ? "Context Surface" : "Internal";
}

function formatTotalElapsedMs(ms: number) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 10000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 1000)}s`;
}

function mergeToolEvents(events: ToolEvent[]): MergedToolEvent[] {
  const merged: MergedToolEvent[] = [];
  for (const ev of events) {
    const prev = merged[merged.length - 1];
    if (ev.status === "result" && prev && prev.toolName === ev.toolName && prev.toolKind === ev.toolKind && prev.resultPayload === undefined) {
      prev.resultPayload = ev.payload;
      prev.durationMs = ev.durationMs ?? prev.durationMs;
      prev.ts = prev.ts ?? ev.ts;
      continue;
    }
    merged.push({
      toolName: ev.toolName, toolKind: ev.toolKind,
      callPayload: ev.status === "call" ? ev.payload : undefined,
      resultPayload: ev.status === "result" ? ev.payload : undefined,
      durationMs: ev.durationMs,
      ts: ev.ts,
    });
  }
  return merged;
}

type TraceTimelineEntry =
  | { kind: "step"; index: number; ts: number; step: ThinkingStep }
  | { kind: "tool"; index: number; ts: number; tool: MergedToolEvent };

function buildTraceTimeline(steps: ThinkingStep[], tools: MergedToolEvent[]): TraceTimelineEntry[] {
  const stepEntries = steps.map((step, index) => ({
    kind: "step" as const,
    index,
    ts: step.ts ?? 0,
    step,
  }));
  const toolEntries = tools.map((tool, index) => ({
    kind: "tool" as const,
    index,
    ts: tool.ts ?? 0,
    tool,
  }));
  return [...stepEntries, ...toolEntries].sort((a, b) => {
    if (a.ts !== b.ts) return a.ts - b.ts;
    if (a.kind !== b.kind) return a.kind === "step" ? -1 : 1;
    return a.index - b.index;
  });
}

function BrandLogo({ src, className = "brand-logo" }: { src?: string; className?: string }) {
  if (!src) {
    return <div className={className} />;
  }
  return (
    <span className={className} aria-hidden="true">
      <img src={src} alt="" />
    </span>
  );
}

function MarkdownMessage({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function extractWrappedContextJson(raw: string): string | null {
  const startMarker = "content='";
  const start = raw.indexOf(startMarker);
  if (start < 0) return null;

  const contentStart = start + startMarker.length;
  let value = "";

  for (let index = contentStart; index < raw.length; index += 1) {
    const char = raw[index];
    const previousChar = index > contentStart ? raw[index - 1] : "";

    if (char === "'" && previousChar !== "\\") {
      return value;
    }

    value += char;
  }

  return null;
}

function parseWrappedContextJson(raw: string): unknown | null {
  const wrapped = extractWrappedContextJson(raw);
  if (!wrapped) return null;

  try {
    return JSON.parse(wrapped.replaceAll("\\'", "'"));
  } catch {
    return null;
  }
}

function normalizeToolPayload(payload: unknown): unknown {
  if (typeof payload === "string") {
    return parseWrappedContextJson(payload) ?? payload;
  }

  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return payload;
  }

  if ("result" in payload && typeof payload.result === "string") {
    return parseWrappedContextJson(payload.result) ?? payload;
  }

  if ("raw_text" in payload && typeof payload.raw_text === "string") {
    return parseWrappedContextJson(payload.raw_text) ?? payload;
  }

  return payload;
}

function JsonToken({ value, className }: { value: string; className?: string }) {
  return <span className={className}>{value}</span>;
}

function renderJsonValue(value: unknown, depth = 0): React.JSX.Element {
  if (value === null) {
    return <JsonToken value="null" className="json-null" />;
  }

  if (typeof value === "string") {
    return <JsonToken value={JSON.stringify(value)} className="json-string" />;
  }

  if (typeof value === "number") {
    return <JsonToken value={String(value)} className="json-number" />;
  }

  if (typeof value === "boolean") {
    return <JsonToken value={String(value)} className="json-boolean" />;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <>
          <JsonToken value="[" className="json-punct" />
          <JsonToken value="]" className="json-punct" />
        </>
      );
    }

    return (
      <>
        <JsonToken value="[" className="json-punct" />
        {value.map((item, index) => (
          <div key={`array-${depth}-${index}`} className="json-line" style={{ paddingLeft: `${(depth + 1) * 1.25}rem` }}>
            {renderJsonValue(item, depth + 1)}
            {index < value.length - 1 && <JsonToken value="," className="json-punct" />}
          </div>
        ))}
        <div className="json-line" style={{ paddingLeft: `${depth * 1.25}rem` }}>
          <JsonToken value="]" className="json-punct" />
        </div>
      </>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value);

    if (entries.length === 0) {
      return (
        <>
          <JsonToken value="{" className="json-punct" />
          <JsonToken value="}" className="json-punct" />
        </>
      );
    }

    return (
      <>
        <JsonToken value="{" className="json-punct" />
        {entries.map(([key, entryValue], index) => (
          <div key={`object-${depth}-${key}`} className="json-line" style={{ paddingLeft: `${(depth + 1) * 1.25}rem` }}>
            <JsonToken value={JSON.stringify(key)} className="json-key" />
            <JsonToken value=": " className="json-punct" />
            {renderJsonValue(entryValue, depth + 1)}
            {index < entries.length - 1 && <JsonToken value="," className="json-punct" />}
          </div>
        ))}
        <div className="json-line" style={{ paddingLeft: `${depth * 1.25}rem` }}>
          <JsonToken value="}" className="json-punct" />
        </div>
      </>
    );
  }

  return <JsonToken value={JSON.stringify(String(value))} className="json-string" />;
}

function ToolPayloadJson({ payload }: { payload: unknown }) {
  const normalized = normalizeToolPayload(payload);

  return (
    <div className="json-scrollbox">
      <div className="json-tree">
        {renderJsonValue(normalized)}
      </div>
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState<HealthState>(null);
  const [domain, setDomain] = useState<DomainConfig>(null);
  const [mode, setMode] = useState<AgentMode>(() => (localStorage.getItem(modeStorageKey) as AgentMode) || "context_surfaces");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(() => crypto.randomUUID());
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const hasMessages = messages.length > 0;

  useEffect(() => {
    void fetch("/api/health")
      .then((r) => r.json())
      .then((p: HealthState) => setHealth(p))
      .catch(() => setHealth({ ok: false, domain: "unknown", mcp_enabled: false, internal_tools: [] }));
  }, []);

  useEffect(() => {
    void fetch("/api/domain-config")
      .then((r) => r.json())
      .then((p: DomainConfig) => setDomain(p))
      .catch(() => setDomain(null));
  }, []);

  useEffect(() => { localStorage.setItem(modeStorageKey, mode); }, [mode]);

  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  useEffect(() => {
    if (!domain) return;
    Object.entries(domain.theme).forEach(([key, value]) => {
      document.documentElement.style.setProperty(`--${key.replaceAll("_", "-")}`, value);
    });
  }, [domain]);

  useEffect(() => {
    document.title = domain?.app_name ?? "Domain Demo";
  }, [domain]);

  async function submitPrompt(prompt: string, event?: FormEvent) {
    event?.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed || isLoading) return;

    const emptyMsg = (): ChatMessage => ({ id: "", role: "assistant", content: "", statusMessages: [], thinkingSteps: [], toolEvents: [] });
    const userMsg: ChatMessage = { ...emptyMsg(), id: `user-${Date.now()}`, role: "user" , content: trimmed };
    const assistantId = `assistant-${Date.now()}`;
    const assistantMsg: ChatMessage = { ...emptyMsg(), id: assistantId };
    const nextMessages = [...messages, userMsg];
    setMessages([...nextMessages, assistantMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages.map(({ role, content }) => ({ role, content })),
          mode,
          thread_id: threadId,
        }),
      });

      if (!response.body) { setIsLoading(false); return; }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const ev = JSON.parse(part.slice(6));
          setMessages((cur) =>
            cur.map((m) => {
              if (m.id !== assistantId) return m;
              switch (ev.type) {
                case "status":
                  return { ...m, statusMessages: [...m.statusMessages, { text: ev.text, ts: ev.ts ?? 0 }] };
                case "thinking-step":
                  return {
                    ...m,
                    thinkingSteps: [...m.thinkingSteps, {
                      id: ev.stepId ?? `step-${m.thinkingSteps.length}-${ev.ts ?? 0}`,
                      text: ev.step,
                      ts: ev.ts ?? 0,
                      kind: ev.stepKind === "llm" ? "llm" : "plan",
                    }],
                  };
                case "thinking-step-finish":
                  return {
                    ...m,
                    thinkingSteps: m.thinkingSteps.map((step) =>
                      step.id === ev.stepId
                        ? {
                            ...step,
                            durationMs: ev.durationMs,
                            durationText: ev.durationText,
                          }
                        : step,
                    ),
                  };
                case "tool-call":
                case "tool-result":
                  return { ...m, toolEvents: [...m.toolEvents, {
                    toolName: ev.toolName, toolKind: ev.toolKind ?? "internal_function",
                    status: ev.type === "tool-call" ? "call" : "result",
                    payload: ev.payload ?? {}, durationMs: ev.durationMs, ts: ev.ts ?? 0,
                  }] };
                case "text-delta":
                  return { ...m, content: m.content + (ev.delta ?? "") };
                case "done":
                  return { ...m, totalElapsedMs: ev.totalElapsedMs };
                default:
                  return m;
              }
            }),
          );
        }
      }
    } catch (err) {
      setMessages((cur) =>
        cur.map((m) => m.id === assistantId ? { ...m, content: m.content || "Connection error. Please try again." } : m),
      );
    }
    setIsLoading(false);
  }

  async function handleSubmit(event?: FormEvent) { await submitPrompt(input, event); }
  function handleQuickStart(prompt: string) { setInput(prompt); void submitPrompt(prompt); }
  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    void handleSubmit();
  }

  return (
    <div className="shell">
      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <div className="brand">
              <BrandLogo src={domain?.logo_src} className="brand-logo" />
              <div className="brand-copy">
                <div className="brand-name">{domain?.app_name ?? "Demo"}</div>
                <div className="brand-subtitle">{domain?.subtitle ?? "Context Surfaces"}</div>
              </div>
            </div>
          </div>
          <div className="mode-toggle">
            <button className={`mode-btn ${mode === "context_surfaces" ? "active" : ""}`} onClick={() => { setMode("context_surfaces"); setMessages([]); setThreadId(crypto.randomUUID()); }} type="button">Context Surfaces</button>
            <button className={`mode-btn ${mode === "simple_rag" ? "active" : ""}`} onClick={() => { setMode("simple_rag"); setMessages([]); setThreadId(crypto.randomUUID()); }} type="button">Simple RAG</button>
          </div>
        </header>

        <section className={`workspace ${hasMessages ? "has-messages" : "is-empty"}`}>
          <div className={`conversation ${hasMessages ? "has-messages" : "is-empty"}`}>
            {!hasMessages && (
              <div className="hero-panel">
                <div className="hero-mark"><BrandLogo src={domain?.logo_src} className="hero-logo" /></div>
                <h1 className="hero-title">{domain?.hero_title ?? "How can we help?"}</h1>
              </div>
            )}

            {messages.map((message) => {
              const toolRows = mergeToolEvents(message.toolEvents);
              const traceTimeline = buildTraceTimeline(message.thinkingSteps, toolRows);
              const isAssistant = message.role === "assistant";
              const lastStatus = isAssistant && message.statusMessages.length > 0 ? message.statusMessages[message.statusMessages.length - 1] : null;
              const showStatus = isAssistant && !message.content && lastStatus;
              return (
                <article key={message.id} className={`message-block ${message.role}`}>
                  {showStatus && (
                    <div className="status-line">⏳ {lastStatus.text}</div>
                  )}
                  {isAssistant && (message.thinkingSteps.length > 0 || toolRows.length > 0) && (
                    <details className="trace-panel" open>
                      <summary className="trace-panel-summary">
                        <span className="trace-title">Agent Trace</span>
                        <span className="trace-counts">
                          {message.thinkingSteps.length > 0 && <span>{message.thinkingSteps.length} steps</span>}
                          {toolRows.length > 0 && <span>{toolRows.length} tool{toolRows.length > 1 ? "s" : ""}</span>}
                        </span>
                      </summary>
                      <div className="trace-panel-body">
                        {traceTimeline.map((entry) => (
                          entry.kind === "step" ? (
                            <div key={`${message.id}-step-${entry.step.id}`} className="trace-line">
                              <span className="trace-pill">{entry.step.kind}</span>
                              <span className="trace-line-text">{entry.step.text}</span>
                              {entry.step.durationText && <span className="trace-latency">{entry.step.durationText}</span>}
                            </div>
                          ) : (
                          <details key={`${message.id}-tool-${entry.index}`} className="tool-item">
                            <summary className="tool-summary">
                              <div className="tool-header">
                                <span className={`tool-source ${entry.tool.toolKind}`}>{toolKindLabel(entry.tool.toolKind)}</span>
                                <span className="tool-name">{entry.tool.toolName}</span>
                              </div>
                              {entry.tool.durationMs !== undefined && <span className="trace-latency">{entry.tool.durationMs}ms</span>}
                            </summary>
                            {entry.tool.callPayload && (
                              <div className="tool-detail-section">
                                <div className="tool-detail-label">Call</div>
                                <ToolPayloadJson payload={entry.tool.callPayload} />
                              </div>
                            )}
                            {entry.tool.resultPayload && (
                              <div className="tool-detail-section">
                                <div className="tool-detail-label">Result</div>
                                <ToolPayloadJson payload={entry.tool.resultPayload} />
                              </div>
                            )}
                          </details>
                          )
                        ))}
                      </div>
                    </details>
                  )}
                  {message.content && (
                    <div className="message-bubble">
                      {message.role === "assistant" ? (
                        <MarkdownMessage content={message.content} />
                      ) : (
                        <div className="plain-text-message">{message.content}</div>
                      )}
                    </div>
                  )}
                  {isAssistant && message.totalElapsedMs !== undefined && (
                    <div className="message-meta">Completed in {formatTotalElapsedMs(message.totalElapsedMs)}</div>
                  )}
                </article>
              );
            })}
            <div ref={scrollRef} />
          </div>

          <form className={`composer ${hasMessages ? "thread" : "hero"}`} onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder={domain?.placeholder_text ?? "Ask a question..."}
            />
            <div className="composer-footer">
              <div className="composer-hint">Press Enter to send</div>
              <button className="send-button" type="submit" disabled={isLoading}>Send</button>
            </div>
          </form>

          {!hasMessages && (
            <div className="quick-starts">
              <div className="quick-starts-label">Try asking</div>
              <div className="quick-starts-row">
                {(domain?.starter_prompts ?? []).map((p) => (
                  <button key={p.title} className="quick-start-chip" onClick={() => handleQuickStart(p.prompt)} type="button">{p.title}</button>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
