export default function StatusBar({ activeAgent }) {
  return (
    <div className="h-12 px-4 flex items-center justify-between
      bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500
      text-white shadow-sm"
    >
      <div className="flex items-center gap-2 text-sm">
        <span className="opacity-90">Active agent</span>
        <span className="px-2.5 py-0.5 rounded-full bg-white/20 backdrop-blur text-xs font-semibold tracking-wide">
          {activeAgent || "-"}
        </span>
      </div>
    </div>
  );
}
