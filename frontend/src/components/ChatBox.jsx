import { useEffect, useRef, useState } from "react";
import client from "../api/client";
import MessageList from "./MessageList";

function uuid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

export default function ChatBox({
  onAgentChange,
  onTimelineUpdate,
  onToolLogsUpdate,
  timeline,
  toolLogs,
  activeAgent
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(() => uuid());
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const restoredRef = useRef(false);

  useEffect(() => {
    if (restoredRef.current) return;
    if (messages.length !== 0) return;

    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);

      setMessages(s.messages || []);
      setConversationId(s.conversationId || uuid());
      onTimelineUpdate(s.timeline || []);
      onToolLogsUpdate(s.toolLogs || []);
      onAgentChange(s.activeAgent || "Idle");

      restoredRef.current = true;
    } catch {}
  }, [messages.length]);

  useEffect(() => {
    localStorage.setItem(
      "agent_chat_ui",
      JSON.stringify({
        messages,
        conversationId,
        timeline,
        toolLogs,
        activeAgent
      })
    );
  }, [messages, conversationId, timeline, toolLogs, activeAgent]);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages, loading]);

  function startNewConversation() {
    const newId = uuid();

    setConversationId(newId);
    setMessages([]);
    setInput("");
    setLoading(false);

    onAgentChange("Idle");
    onTimelineUpdate([]);
    onToolLogsUpdate([]);

    localStorage.removeItem("agent_chat_ui");
    restoredRef.current = false;
  }

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();

    setMessages(prev => [
      ...prev,
      { role: "user", text: userMsg, ts: Date.now() }
    ]);

    setInput("");
    setLoading(true);

    try {
      const res = await client.post("/chat", {
        conversation_id: conversationId,
        user_message: userMsg
      });

      const data = res.data;

      if (Array.isArray(data.trace)) {
        const lastAgent = [...data.trace]
          .reverse()
          .find(e => e.type === "agent");

        if (lastAgent) onAgentChange(lastAgent.name);

        onTimelineUpdate(prev => [...prev, ...data.trace]);

        const tools = data.trace.filter(e => e.type === "tool");
        onToolLogsUpdate(prev => [...prev, ...tools]);
      }

      
      if (data.reply) {
        setMessages(prev => [
          ...prev,
          { role: "assistant", text: data.reply, ts: Date.now() }
        ]);
      }

    } catch {
      setMessages(prev => [
        ...prev,
        { role: "assistant", text: "Server error.", ts: Date.now() }
      ]);
    }

    setLoading(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="h-full flex flex-col rounded-3xl overflow-hidden shadow-xl bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <div className="px-5 py-3 flex items-center justify-between bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500 text-white shadow">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shadow">
            💬
          </div>
          <div className="font-semibold text-sm tracking-wide">
            Interview Assistant
          </div>
        </div>

        <button
          onClick={startNewConversation}
          className="text-xs px-4 py-1.5 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur transition shadow"
        >
          New chat
        </button>
      </div>

      <div ref={containerRef} className="flex-1 overflow-y-auto px-5 py-4">
        {messages.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-slate-700 text-sm gap-2">
            <div className="text-3xl">🤖</div>
            Start a conversation to schedule an interview
          </div>
        )}

        {messages.length > 0 && <MessageList messages={messages} />}

        {loading && (
          <div className="flex items-center gap-2 mt-4">
            <span className="h-2.5 w-2.5 rounded-full bg-indigo-500 animate-bounce" />
            <span className="h-2.5 w-2.5 rounded-full bg-sky-500 animate-bounce [animation-delay:150ms]" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:300ms]" />
            <span className="text-xs text-slate-700 ml-2">
              Assistant is typing…
            </span>
          </div>
        )}
      </div>

      <div className="p-3 bg-gradient-to-r from-indigo-100 via-sky-100 to-emerald-100 backdrop-blur">
        <div className="flex gap-2 items-end">
          <textarea
            rows={1}
            className="flex-1 resize-none rounded-2xl bg-white/70 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-400 max-h-32 shadow-inner"
            placeholder="Type your message…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="h-10 px-6 rounded-2xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
          >
            Send
          </button>
        </div>

        <div className="mt-1 text-[11px] text-slate-600 text-right">
          Enter to send · Shift + Enter for new line
        </div>
      </div>
    </div>
  );
}
