import { useEffect, useRef, useState } from "react";
import client from "../api/client";
import MessageList from "./MessageList";

export default function ChatBox({
  onAgentChange,
  onTimelineUpdate,
  onToolLogsUpdate
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(() =>
    crypto.randomUUID()
  );
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages, loading]);

  function startNewConversation() {
    setConversationId(crypto.randomUUID());
    setMessages([]);
    setInput("");
    onAgentChange("-");
    onTimelineUpdate([]);
    onToolLogsUpdate([]);
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

      if (data.success === true && data.interview_id) {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            text: "Interview scheduled successfully.",
            ts: Date.now()
          }
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
    <div className="h-full flex flex-col rounded-2xl overflow-hidden shadow-sm border border-slate-200/60 bg-gradient-to-br from-indigo-50 via-sky-50 to-emerald-50">
      <div className="px-4 py-2.5 flex items-center justify-between bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 text-white">
        <div className="font-semibold text-sm tracking-wide">
          Interview Assistant
        </div>

        <button
          onClick={startNewConversation}
          className="text-xs px-3 py-1.5 rounded-full bg-white/15 hover:bg-white/25 backdrop-blur border border-white/20 transition"
        >
          New chat
        </button>
      </div>

      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        {messages.length === 0 && !loading && (
          <div className="h-full flex items-center justify-center text-slate-400 text-sm">
            Start a conversation to schedule an interview
          </div>
        )}

        {messages.length > 0 && (
          <div className="space-y-3">
            <MessageList messages={messages} />
          </div>
        )}

        {loading && (
          <div className="flex items-center gap-2 mt-4">
            <span className="h-2.5 w-2.5 rounded-full bg-indigo-500 animate-bounce" />
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-500 animate-bounce [animation-delay:150ms]" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:300ms]" />
            <span className="text-xs text-slate-600 ml-2">
              Assistant is typing…
            </span>
          </div>
        )}
      </div>

      <div className="p-3 bg-white/80 backdrop-blur border-t border-slate-200/60">
        <div className="flex gap-2 items-end">
          <textarea
            rows={1}
            className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500/40 max-h-32"
            placeholder="Type your message…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="h-10 px-5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition shadow"
          >
            Send
          </button>
        </div>

        <div className="mt-1 text-[11px] text-slate-500 text-right">
          Enter to send · Shift + Enter for new line
        </div>
      </div>
    </div>
  );
}
