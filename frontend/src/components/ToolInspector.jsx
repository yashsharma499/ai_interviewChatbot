export default function ToolInspector({ items }) {
  return (
    <div
      className="h-64 overflow-y-auto p-4
      bg-gradient-to-br from-indigo-50 via-sky-50 to-emerald-50"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-slate-700">
          Tool inspector
        </div>

        <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
          {items.length}
        </span>
      </div>

      <div className="space-y-3">
        {items.map((t, i) => {
          const ok = t.status === "success";

          return (
            <div
              key={i}
              className="rounded-xl border border-slate-200/60 bg-white shadow-sm overflow-hidden transition hover:shadow-md"
            >
              <div className="px-3 py-2 flex items-center justify-between bg-gradient-to-r from-emerald-50 to-cyan-50 border-b border-slate-200/60">
                <div className="text-xs font-semibold text-slate-700 truncate">
                  {t.tool_name}
                </div>

                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium
                    ${
                      ok
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-rose-100 text-rose-700"
                    }`}
                >
                  {t.status}
                </span>
              </div>

              <div className="px-3 py-2">
                <div className="text-[11px] text-slate-500 mb-2">
                  {t.started_at} → {t.finished_at}
                </div>

                <pre className="text-[11px] leading-snug bg-slate-50 border border-slate-200/60 rounded-lg p-2 overflow-x-auto">
{JSON.stringify({ input: t.input }, null, 2)}
                </pre>
              </div>
            </div>
          );
        })}

        {items.length === 0 && (
          <div className="h-24 flex items-center justify-center text-slate-400 text-xs">
            No tools used yet
          </div>
        )}
      </div>
    </div>
  );
}
