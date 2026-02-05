import { useEffect, useRef, useState } from "react";

export default function Timeline({ items }) {
  const [value, setValue] = useState(items || []);
  const restoredRef = useRef(false);

  useEffect(() => {
    if (restoredRef.current) return;
    if ((items || []).length !== 0) return;

    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);
      if (Array.isArray(s.timeline)) {
        setValue(s.timeline);
        restoredRef.current = true;
      }
    } catch {}
  }, [items?.length]);

  useEffect(() => {
    if (!Array.isArray(items)) return;

    setValue(items);

    if (items.length === 0) {
      restoredRef.current = false;
    }
  }, [items]);

  useEffect(() => {
    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);
      s.timeline = value;
      localStorage.setItem("agent_chat_ui", JSON.stringify(s));
    } catch {}
  }, [value]);

  const agentItems = (value || []).filter(t => t.type === "agent");

  return (
    <div className="custom-scroll flex-1 overflow-y-auto p-4 bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <style>{`
        .custom-scroll::-webkit-scrollbar {
          width: 12px;
        }

        .custom-scroll::-webkit-scrollbar-track {
          background: linear-gradient(
            180deg,
            rgba(99,102,241,0.15),
            rgba(56,189,248,0.15),
            rgba(52,211,153,0.15)
          );
          border-radius: 999px;
        }

        .custom-scroll::-webkit-scrollbar-thumb {
          border-radius: 999px;
          background: linear-gradient(
            180deg,
            #6366f1,
            #38bdf8,
            #34d399
          );
          border: 3px solid rgba(255,255,255,0.6);
          background-clip: padding-box;
        }

        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(
            180deg,
            #4f46e5,
            #0ea5e9,
            #10b981
          );
        }

        .custom-scroll {
          scrollbar-width: thin;
          scrollbar-color: #38bdf8 rgba(99,102,241,0.15);
        }
      `}</style>

      <div className="h-full rounded-3xl bg-gradient-to-br from-indigo-500/10 via-sky-500/10 to-emerald-500/10 shadow-xl backdrop-blur p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 text-white flex items-center justify-center shadow">
              🤖
            </div>
            <div className="text-sm font-semibold text-slate-800">
              Agent timeline
            </div>
          </div>

          <span className="text-[11px] px-3 py-1 rounded-full font-semibold bg-gradient-to-r from-indigo-400 to-cyan-400 text-white shadow">
            {agentItems.length}
          </span>
        </div>

        <div className="relative pl-6">
          <div className="absolute left-[14px] top-0 bottom-0 w-[2px] bg-gradient-to-b from-indigo-400 via-sky-400 to-emerald-400 rounded-full" />

          {agentItems.map((t, i) => (
            <div
              key={i}
              className="relative mb-3 rounded-2xl px-4 py-2 bg-gradient-to-r from-indigo-50/80 to-sky-50/80 hover:from-indigo-100 hover:to-sky-100 transition shadow-sm"
            >
              <div className="absolute left-[6px] top-4 h-3.5 w-3.5 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-400 ring-2 ring-white shadow" />

              <div className="ml-6">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[11px] font-semibold text-indigo-600">
                    agent
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {t.timestamp}
                  </span>
                </div>

                <div className="text-sm text-slate-800 leading-snug">
                  {t.name}
                </div>
              </div>
            </div>
          ))}

          {agentItems.length === 0 && (
            <div className="h-28 flex flex-col items-center justify-center text-slate-600 text-xs gap-2">
              <div className="text-2xl">🕒</div>
              No activity yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
