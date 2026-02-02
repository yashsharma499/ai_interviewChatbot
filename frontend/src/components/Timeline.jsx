export default function Timeline({ items }) {

  const agentItems = (items || []).filter(t => t.type === "agent");

  return (
    <div
      className="flex-1 overflow-y-auto p-4
      bg-gradient-to-br from-indigo-50 via-sky-50 to-emerald-50"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-slate-700">
          Agent timeline
        </div>
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
          {agentItems.length}
        </span>
      </div>

      <div className="relative pl-4">
        <div className="absolute left-[6px] top-0 bottom-0 w-px bg-gradient-to-b from-indigo-300 via-blue-300 to-cyan-300" />

        {agentItems.map((t, i) => (
          <div
            key={i}
            className="relative mb-3 rounded-lg px-2 py-1 transition hover:bg-white/60"
          >
            <div
              className="absolute left-[-2px] top-2 h-3 w-3 rounded-full ring-2 ring-white bg-indigo-500"
            />

            <div className="ml-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-indigo-600">
                  agent
                </span>

                <span className="text-[10px] text-slate-400">
                  {t.timestamp}
                </span>
              </div>

              <div className="text-sm text-slate-700 leading-snug">
                {t.name}
              </div>
            </div>
          </div>
        ))}

        {agentItems.length === 0 && (
          <div className="h-24 flex items-center justify-center text-slate-400 text-xs">
            No activity yet
          </div>
        )}
      </div>
    </div>
  );
}
