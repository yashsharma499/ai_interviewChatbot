import { useState } from "react";
import InterviewAssistant from "./pages/InterviewAssistant";
import CalendarView from "./pages/CalendarView";

function App() {
  const [page, setPage] = useState("assistant");

  const isAssistant = page === "assistant";
  const isCalendar = page === "calendar";

  return (
    <div
      className="h-screen flex flex-col
      bg-gradient-to-br
      from-indigo-100 via-sky-100 to-emerald-100"
    >
      <div className="border-b bg-white/85 backdrop-blur px-3 py-2 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage('assistant')}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition
              ${
                isAssistant
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-500 text-white shadow"
                  : "bg-white border text-slate-600 hover:bg-slate-50"
              }`}
          >
            Interview assistant
          </button>

          <button
            onClick={() => setPage('calendar')}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition
              ${
                isCalendar
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-500 text-white shadow"
                  : "bg-white border text-slate-600 hover:bg-slate-50"
              }`}
          >
            Calendar
          </button>
        </div>

        <div className="text-xs text-slate-500 hidden sm:block">
          Interview scheduling console
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {isAssistant && <InterviewAssistant />}
        {isCalendar && <CalendarView />}
      </div>
    </div>
  );
}

export default App;
