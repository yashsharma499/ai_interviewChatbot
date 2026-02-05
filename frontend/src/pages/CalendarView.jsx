import { useEffect, useMemo, useState } from "react";
import client from "../api/client";

export default function CalendarView() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await client.get("/interviews");
        setItems(res.data || []);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();

    return items.filter(r =>
      String(r.id).toLowerCase().includes(q) ||
      String(r.candidate_name || "").toLowerCase().includes(q) ||
      String(r.interviewer_id).toLowerCase().includes(q)
    );
  }, [items, query]);

  function formatTime(value) {
    if (!value) return "-";

    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;

    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true
    });
  }

  return (
    <div className="h-full p-4 bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <div className="h-full flex flex-col rounded-3xl bg-gradient-to-br from-indigo-500/10 via-sky-500/10 to-emerald-500/10 shadow-xl backdrop-blur">
        <div className="px-6 py-5">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-400 text-white flex items-center justify-center shadow-lg text-xl">
              📅
            </div>

            <div className="flex-1">
              <div className="text-lg font-semibold text-slate-900">
                Scheduled interviews
              </div>
              <div className="text-xs text-slate-700">
                Manage and monitor interview schedules
              </div>
            </div>

            <div className="px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-indigo-400 to-cyan-400 text-white shadow">
              {filtered.length}
            </div>
          </div>
        </div>

        <div className="px-6 pb-4">
          <div className="relative">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search by ID, candidate or interviewer..."
              className="w-full h-11 rounded-2xl bg-gradient-to-r from-sky-100 to-indigo-100 pl-11 pr-4 text-sm text-slate-800 placeholder-slate-500 outline-none focus:ring-2 focus:ring-indigo-400 shadow-md"
            />
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-600 text-lg">
              🔍
            </span>
          </div>
        </div>

        <div className="flex-1 px-6 pb-6">
          <div className="h-full rounded-3xl bg-gradient-to-br from-indigo-100 via-sky-100 to-emerald-100 shadow-lg overflow-hidden">
            {loading && (
              <div className="p-6 space-y-3 animate-pulse">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-8 rounded-xl bg-indigo-200/60" />
                ))}
              </div>
            )}

            {!loading && filtered.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 text-sm gap-2">
                <div className="text-4xl">🗂️</div>
                No interviews found
              </div>
            )}

            {!loading && filtered.length > 0 && (
              <div className="h-full overflow-auto">
                <table className="min-w-full text-sm">
                  <thead className="sticky top-0 z-10">
                    <tr className="bg-gradient-to-r from-indigo-400 via-sky-400 to-emerald-400 text-white">
                      <th className="px-5 py-3 text-left font-semibold">#</th>
                      <th className="px-5 py-3 text-left font-semibold">Candidate</th>
                      <th className="px-5 py-3 text-left font-semibold">Interviewer</th>
                      <th className="px-5 py-3 text-left font-semibold">Time</th>
                      <th className="px-5 py-3 text-left font-semibold">Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filtered.map((row, idx) => {
                      const ok =
                        row.status?.toLowerCase?.() === "scheduled";

                      const candidateName =
                        row.candidate_name || String(row.candidate_id || "");

                      return (
                        <tr
                          key={row.id}
                          className={`transition hover:scale-[1.005] hover:shadow-md ${
                            idx % 2 === 0
                              ? "bg-gradient-to-r from-indigo-50 to-sky-50"
                              : "bg-gradient-to-r from-sky-50 to-emerald-50"
                          }`}
                        >
                          <td className="px-5 py-3 font-medium text-slate-800">
                            {idx + 1}
                          </td>

                          <td className="px-5 py-3 text-slate-800">
                            {candidateName}
                          </td>

                          <td className="px-5 py-3 text-slate-800">
                            {row.interviewer_id}
                          </td>

                          <td className="px-5 py-3 whitespace-nowrap text-slate-700">
                            {formatTime(row.scheduled_time)}
                          </td>

                          <td className="px-5 py-3">
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-semibold shadow-sm ${
                                ok
                                  ? "bg-gradient-to-r from-emerald-400 to-green-400 text-white"
                                  : "bg-gradient-to-r from-amber-400 to-orange-400 text-white"
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
