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
              className={`max-w-[75%] px-4 py-2.5 text-sm leading-relaxed rounded-2xl shadow-sm
                ${
                  isUser
                    ? "bg-gradient-to-br from-indigo-500 via-blue-500 to-cyan-500 text-white rounded-br-md"
                    : "bg-white border border-slate-200 text-slate-700 rounded-bl-md"
                }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {m.text}
              </div>

              {m.ts && (
                <div
                  className={`mt-1 text-[10px] ${
                    isUser ? "text-white/70" : "text-slate-400"
                  } text-right`}
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
