export default function MessageList({ messages }) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((m, i) => {
        const isUser = m.role === "user";

        return (
          <div
            key={i}
            className={`flex ${isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] px-4 py-2.5 text-sm leading-relaxed rounded-2xl shadow-md transition
                ${
                  isUser
                    ? "bg-gradient-to-br from-indigo-500 via-sky-500 to-emerald-500 text-white rounded-br-md"
                    : "bg-gradient-to-br from-indigo-100 via-sky-100 to-emerald-100 text-slate-800 rounded-bl-md"
                }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {m.text}
              </div>

              {m.ts && (
                <div
                  className={`mt-1 text-[10px] text-right ${
                    isUser ? "text-white/80" : "text-slate-600"
                  }`}
                >
                  {new Date(m.ts).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit"
                  })}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
