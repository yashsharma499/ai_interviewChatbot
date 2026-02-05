import { useEffect, useState } from "react";

export default function StatusBar({ activeAgent }) {
  const [value, setValue] = useState(activeAgent || "Idle");

  useEffect(() => {
    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);
      if (s.activeAgent) setValue(s.activeAgent);
    } catch {}
  }, []);

  useEffect(() => {
    if (!activeAgent) return;
    setValue(activeAgent);
  }, [activeAgent]);

  useEffect(() => {
    const saved = localStorage.getItem("agent_chat_ui");
    if (!saved) return;

    try {
      const s = JSON.parse(saved);
      s.activeAgent = value;
      localStorage.setItem("agent_chat_ui", JSON.stringify(s));
    } catch {}
  }, [value]);

  return (
    <div className="h-12 px-5 flex items-center justify-between bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500 text-white shadow-lg rounded-b-3xl">
      <div className="flex items-center gap-3 text-sm">
        <div className="h-7 w-7 rounded-lg bg-white/20 backdrop-blur flex items-center justify-center shadow">
          🤖
        </div>

        <span className="opacity-90">Active agent</span>

        <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur text-xs font-semibold tracking-wide shadow">
          {value || "Idle"}
        </span>
      </div>
    </div>
  );
}


