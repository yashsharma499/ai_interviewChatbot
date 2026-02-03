import { useState } from "react";
import InterviewAssistant from "./pages/InterviewAssistant";
import CalendarView from "./pages/CalendarView";

function App() {
  const [page, setPage] = useState("assistant");

  const isAssistant = page === "assistant";
  const isCalendar = page === "calendar";

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <div
        className="
          px-4 py-3 flex items-center justify-between
          bg-gradient-to-r from-indigo-600 via-sky-600 to-teal-500
          shadow-xl
        "
      >
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage("assistant")}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold transition shadow
              ${
                isAssistant
                  ? "bg-white/30 text-white backdrop-blur"
                  : "bg-white/10 text-white/80 hover:bg-white/20 backdrop-blur"
              }`}
          >
            🤖 Assistant
          </button>

          <button
            onClick={() => setPage("calendar")}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold transition shadow
              ${
                isCalendar
                  ? "bg-white/30 text-white backdrop-blur"
                  : "bg-white/10 text-white/80 hover:bg-white/20 backdrop-blur"
              }`}
          >
            📅 Calendar
          </button>
        </div>

        <div className="text-xs text-white/85 hidden sm:block">
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
