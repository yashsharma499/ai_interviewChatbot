import { useEffect, useState } from "react";
import client from "../api/client";

export default function CalendarView() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="h-full p-4 bg-gradient-to-br from-indigo-50 via-sky-50 to-emerald-50">
      <div className="h-full flex flex-col rounded-2xl bg-white/90 backdrop-blur border shadow-md p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-semibold text-slate-700">
            Scheduled interviews
          </div>

          <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
            {items.length}
          </span>
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <span className="h-2.5 w-2.5 rounded-full bg-indigo-500 animate-bounce" />
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-500 animate-bounce [animation-delay:150ms]" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:300ms]" />
            <span className="ml-2">Loading interviews…</span>
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
            No interviews scheduled
          </div>
        )}

        {!loading && items.length > 0 && (
          <div className="flex-1 overflow-auto rounded-xl border bg-white shadow-sm">
            <table className="min-w-full text-xs">
              <thead className="sticky top-0 z-10">
                <tr className="bg-gradient-to-r from-indigo-50 to-cyan-50 text-slate-700">
                  <th className="px-3 py-2 text-left font-semibold">ID</th>
                  <th className="px-3 py-2 text-left font-semibold">
                    Candidate
                  </th>
                  <th className="px-3 py-2 text-left font-semibold">
                    Interviewer
                  </th>
                  <th className="px-3 py-2 text-left font-semibold">
                    Scheduled time (UTC)
                  </th>
                  <th className="px-3 py-2 text-left font-semibold">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {items.map((row, idx) => {
                  const ok =
                    row.status?.toLowerCase?.() === "scheduled";

                  return (
                    <tr
                      key={row.id}
                      className={
                        idx % 2 === 0
                          ? "bg-white"
                          : "bg-slate-50/60"
                      }
                    >
                      <td className="px-3 py-2 border-t">
                        {row.id}
                      </td>
                      <td className="px-3 py-2 border-t">
                        {row.candidate_id}
                      </td>
                      <td className="px-3 py-2 border-t">
                        {row.interviewer_id}
                      </td>
                      <td className="px-3 py-2 border-t whitespace-nowrap">
                        {row.scheduled_time}
                      </td>
                      <td className="px-3 py-2 border-t">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            ok
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-amber-100 text-amber-700"
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
  );
}
