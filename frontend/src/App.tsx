import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type ChatRole = "user" | "assistant";

type ToolEvent = {
  toolName: string;
  toolKind: "internal_function" | "mcp_tool";
  status: "call" | "result";
  payload: Record<string, unknown>;
  durationMs?: number;
};

type MergedToolEvent = {
  toolName: string;
  toolKind: ToolEvent["toolKind"];
  callPayload?: Record<string, unknown>;
  resultPayload?: Record<string, unknown>;
  durationMs?: number;
};

type ThinkingStep = { text: string; ts?: number };

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
  mcp_enabled: boolean;
  internal_tools: string[];
} | null;

type AgentMode = "context_surfaces" | "simple_rag";

type PromptCard = { eyebrow: string; title: string; prompt: string };

const modeStorageKey = "reddish-mode";

const starterPrompts: PromptCard[] = [
  { eyebrow: "Order Status", title: "Why is my order running late?", prompt: "Why is my order running late?" },
  { eyebrow: "Order History", title: "Show me my recent orders", prompt: "Show me my order history" },
  { eyebrow: "Policy", title: "What's your refund policy for late deliveries?", prompt: "What is your refund policy for late deliveries?" },
  { eyebrow: "Search", title: "Find me a good sushi restaurant", prompt: "Can you find me a good sushi restaurant?" },
];

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
      continue;
    }
    merged.push({
      toolName: ev.toolName, toolKind: ev.toolKind,
      callPayload: ev.status === "call" ? ev.payload : undefined,
      resultPayload: ev.status === "result" ? ev.payload : undefined,
      durationMs: ev.durationMs,
    });
  }
  return merged;
}

function ReddishLogo({ className = "brand-logo" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="40" height="40" rx="12" fill="#FF4438" />
      <path d="M12 28V14l8 7 8-7v14" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function App() {
  const [health, setHealth] = useState<HealthState>(null);
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
      .catch(() => setHealth({ ok: false, mcp_enabled: false, internal_tools: [] }));
  }, []);

  useEffect(() => { localStorage.setItem(modeStorageKey, mode); }, [mode]);

  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

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
                  return { ...m, thinkingSteps: [...m.thinkingSteps, { text: ev.step, ts: ev.ts }] };
                case "tool-call":
                case "tool-result":
                  return { ...m, toolEvents: [...m.toolEvents, {
                    toolName: ev.toolName, toolKind: ev.toolKind ?? "internal_function",
                    status: ev.type === "tool-call" ? "call" : "result",
                    payload: ev.payload ?? {}, durationMs: ev.durationMs,
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
              <ReddishLogo className="brand-logo" />
              <div className="brand-copy">
                <div className="brand-name">Reddish</div>
                <div className="brand-subtitle">Delivery Support</div>
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
                <div className="hero-mark"><ReddishLogo className="hero-logo" /></div>
                <h1 className="hero-title">How can we help?</h1>
              </div>
            )}

            {messages.map((message) => {
              const toolRows = mergeToolEvents(message.toolEvents);
              const isAssistant = message.role === "assistant";
              const lastStatus = isAssistant && message.statusMessages.length > 0 ? message.statusMessages[message.statusMessages.length - 1] : null;
              const showStatus = isAssistant && !message.content && lastStatus;
              return (
                <article key={message.id} className={`message-block ${message.role}`}>
                  {showStatus && (
                    <div className="status-line">⏳ {lastStatus.text}</div>
                  )}
                  {message.content && <div className="message-bubble">{message.content}</div>}
                  {isAssistant && message.totalElapsedMs !== undefined && (
                    <div className="message-meta">Completed in {formatTotalElapsedMs(message.totalElapsedMs)}</div>
                  )}
                  {isAssistant && (message.thinkingSteps.length > 0 || toolRows.length > 0) && (
                    <details className="trace-panel">
                      <summary className="trace-panel-summary">
                        <span className="trace-title">Agent Trace</span>
                        <span className="trace-counts">
                          {message.thinkingSteps.length > 0 && <span>{message.thinkingSteps.length} steps</span>}
                          {toolRows.length > 0 && <span>{toolRows.length} tool{toolRows.length > 1 ? "s" : ""}</span>}
                        </span>
                      </summary>
                      <div className="trace-panel-body">
                        {message.thinkingSteps.map((step, i) => (
                          <div key={`${message.id}-step-${i}`} className="trace-line">
                            <span className="trace-pill">plan</span>
                            <span className="trace-line-text">{step.text}</span>
                          </div>
                        ))}
                        {toolRows.map((ev, i) => (
                          <details key={`${message.id}-tool-${i}`} className="tool-item">
                            <summary className="tool-summary">
                              <div className="tool-header">
                                <span className={`tool-source ${ev.toolKind}`}>{toolKindLabel(ev.toolKind)}</span>
                                <span className="tool-name">{ev.toolName}</span>
                              </div>
                              {ev.durationMs !== undefined && <span className="trace-latency">{ev.durationMs}ms</span>}
                            </summary>
                            {ev.callPayload && (
                              <div className="tool-detail-section">
                                <div className="tool-detail-label">Call</div>
                                <pre>{JSON.stringify(ev.callPayload, null, 2)}</pre>
                              </div>
                            )}
                            {ev.resultPayload && (
                              <div className="tool-detail-section">
                                <div className="tool-detail-label">Result</div>
                                <pre>{JSON.stringify(ev.resultPayload, null, 2)}</pre>
                              </div>
                            )}
                          </details>
                        ))}
                      </div>
                    </details>
                  )}
                </article>
              );
            })}
            <div ref={scrollRef} />
          </div>

          <form className={`composer ${hasMessages ? "thread" : "hero"}`} onSubmit={handleSubmit}>
            <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleComposerKeyDown} placeholder="Ask about your order, delivery status, or policies..." />
            <div className="composer-footer">
              <div className="composer-hint">Press Enter to send</div>
              <button className="send-button" type="submit" disabled={isLoading}>Send</button>
            </div>
          </form>

          {!hasMessages && (
            <div className="quick-starts">
              <div className="quick-starts-label">Try asking</div>
              <div className="quick-starts-row">
                {starterPrompts.map((p) => (
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

