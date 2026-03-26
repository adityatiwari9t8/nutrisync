import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import api, { getErrorMessage } from "../api/api";
import MacroBar from "../components/MacroBar";

export default function Tracker() {
  const [daily, setDaily] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadTracker = async () => {
      setLoading(true);
      setError("");
      try {
        const [dailyResponse, historyResponse] = await Promise.all([
          api.get("/tracker/daily"),
          api.get("/tracker/history"),
        ]);
        setDaily(dailyResponse.data);
        setHistory(historyResponse.data.history || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Unable to load tracker data."));
      } finally {
        setLoading(false);
      }
    };

    loadTracker();
  }, []);

  const bars = [
    { label: "Protein", value: daily?.totals?.protein || 0, goal: daily?.goals?.protein || 0, accent: "bg-brand" },
    { label: "Carbs", value: daily?.totals?.carbs || 0, goal: daily?.goals?.carbs || 0, accent: "bg-emerald-500" },
    { label: "Fat", value: daily?.totals?.fat || 0, goal: daily?.goals?.fat || 0, accent: "bg-lime-500" },
    { label: "Calories", value: daily?.totals?.calories || 0, goal: daily?.goals?.calories || 0, accent: "bg-emerald-700" },
  ];

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Macro tracker</h1>
        <p className="mt-3 text-base text-mist">
          Review your day at a glance and track how each logged meal contributes to your goals.
        </p>
        {error ? <p className="mt-6 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="surface-card p-6">
          <h2 className="section-title">Today vs goals</h2>
          <div className="mt-6 space-y-5">
            {bars.map((bar) => (
              <MacroBar key={bar.label} {...bar} />
            ))}
          </div>
        </div>

        <div className="surface-card p-6">
          <h2 className="section-title">7-Day History</h2>
          <div className="mt-6 h-72">
            {loading ? (
              <div className="flex h-full items-center justify-center text-sm text-mist">Loading history...</div>
            ) : history.some((point) => point.calories > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid stroke="#d7e7db" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: "#6c7c72", fontSize: 12 }} tickLine={false} />
                  <YAxis tick={{ fill: "#6c7c72", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="protein" stroke="#1a7a4a" strokeWidth={3} dot={false} />
                  <Line type="monotone" dataKey="carbs" stroke="#2f9f69" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="fat" stroke="#5ac48a" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="calories" stroke="#0d5a34" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-sand bg-white/70 px-6 text-center text-sm text-mist">
                Your trend line appears as soon as you build up a few days of meal history.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="surface-card p-6">
        <h2 className="section-title">Logged meals</h2>
        <div className="mt-6 space-y-3">
          {daily?.meals?.length ? (
            daily.meals.map((meal) => (
              <div key={meal.id} className="flex flex-col gap-2 rounded-[22px] bg-white/80 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-ink">{meal.recipe_name}</p>
                  <p className="mt-1 text-sm text-mist">
                    {new Date(meal.date).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold text-brand">
                  <span className="rounded-full bg-brand/10 px-3 py-1">P {Math.round(meal.protein_logged)}g</span>
                  <span className="rounded-full bg-brand/10 px-3 py-1">C {Math.round(meal.carbs_logged)}g</span>
                  <span className="rounded-full bg-brand/10 px-3 py-1">F {Math.round(meal.fat_logged)}g</span>
                  <span className="rounded-full bg-brand/10 px-3 py-1">{Math.round(meal.calories_logged)} kcal</span>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
              Nothing is logged for today yet. Choose a recommendation and save it here in one tap.
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );
}
