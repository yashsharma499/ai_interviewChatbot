import { useEffect, useRef, useState } from "react";

export default function ToolInspector({ items }) {
  const [value, setValue] = useState(items || []);
  const restoredRef = useRef(false);

  useEffect(() => {
    if (restoredRef.current) return;
    if ((items || []).length !== 0) return;

    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);
      if (Array.isArray(s.toolLogs)) {
        setValue(s.toolLogs);
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
      s.toolLogs = value;
      localStorage.setItem("agent_chat_ui", JSON.stringify(s));
    } catch {}
  }, [value]);

  return (
    <div className="h-64 overflow-y-auto p-4 bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <div className="h-full rounded-3xl bg-gradient-to-br from-indigo-500/10 via-sky-500/10 to-emerald-500/10 shadow-xl backdrop-blur p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400 text-white flex items-center justify-center shadow">
              🛠️
            </div>
            <div className="text-sm font-semibold text-slate-800">
              Tool inspector
            </div>
          </div>

          <span className="text-[11px] px-3 py-1 rounded-full font-semibold bg-gradient-to-r from-emerald-400 to-cyan-400 text-white shadow">
            {value.length}
          </span>
        </div>

        <div className="space-y-3">
          {value.map((t, i) => {
            const ok = t.status === "success";

            return (
              <div
                key={i}
                className="rounded-2xl bg-gradient-to-br from-indigo-50/80 to-sky-50/80 shadow-md hover:shadow-lg transition overflow-hidden"
              >
                <div className="px-4 py-2 flex items-center justify-between bg-gradient-to-r from-emerald-400/20 to-cyan-400/20">
                  <div className="text-xs font-semibold text-slate-800 truncate">
                    {t.tool_name}
                  </div>

                  <span
                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-semibold shadow ${
                      ok
                        ? "bg-gradient-to-r from-emerald-400 to-green-400 text-white"
                        : "bg-gradient-to-r from-rose-400 to-pink-400 text-white"
                    }`}
                  >
                    {t.status}
                  </span>
                </div>

                <div className="px-4 py-2">
                  <div className="text-[11px] text-slate-600 mb-2">
                    {t.started_at} → {t.finished_at}
                  </div>

                  <pre className="text-[11px] leading-snug bg-gradient-to-br from-indigo-100 to-sky-100 rounded-xl p-3 overflow-x-auto text-slate-800 shadow-inner">
{JSON.stringify({ input: t.input }, null, 2)}
                  </pre>
                </div>
              </div>
            );
          })}

          {value.length === 0 && (
            <div className="h-24 flex flex-col items-center justify-center text-slate-600 text-xs gap-2">
              <div className="text-2xl">🧰</div>
              No tools used yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
