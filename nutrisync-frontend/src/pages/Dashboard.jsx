import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import api, { getErrorMessage } from "../api/api";
import MacroRing from "../components/MacroRing";

export default function Dashboard({ user }) {
  const [daily, setDaily] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
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
        setError(getErrorMessage(requestError, "Unable to load your dashboard."));
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const rings = [
    { label: "Protein", value: daily?.totals?.protein || 0, goal: daily?.goals?.protein || 0, color: "#1a7a4a" },
    { label: "Carbs", value: daily?.totals?.carbs || 0, goal: daily?.goals?.carbs || 0, color: "#2f9f69" },
    { label: "Fat", value: daily?.totals?.fat || 0, goal: daily?.goals?.fat || 0, color: "#5ac48a" },
    { label: "Calories", value: daily?.totals?.calories || 0, goal: daily?.goals?.calories || 0, color: "#0d5a34" },
  ];
  const calorieProgress =
    daily?.goals?.calories && daily.goals.calories > 0
      ? Math.min(Math.round((daily.totals.calories / daily.goals.calories) * 100), 100)
      : 0;

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card overflow-hidden p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Daily command center</p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-5xl">
              Hello, {user?.username}. Build today&apos;s meals from what is already in your kitchen.
            </h1>
            <p className="mt-4 max-w-2xl text-base text-mist">
              Start with a quick pantry scan, review your pantry intelligence, and move into ranked
              meal ideas designed around your targets, preferences, and what your kitchen can actually support tonight.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/pantry" className="primary-button">
                Open Pantry Intelligence
              </Link>
              <Link to="/recipes" className="secondary-button">
                View Recommendations
              </Link>
            </div>
          </div>

          <div className="surface-card bg-white/80 p-5">
            <p className="text-sm font-semibold text-ink">Today&apos;s snapshot</p>
            <p className="mt-2 text-sm text-mist">
              {daily?.meals?.length
                ? `${daily.meals.length} meals logged today`
                : "No meals logged yet. Start with a pantry scan."}
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[20px] bg-surface px-4 py-3">
                <p className="text-xs uppercase tracking-[0.18em] text-mist">Calorie pace</p>
                <p className="mt-2 text-xl font-bold text-ink">{calorieProgress}%</p>
              </div>
              <div className="rounded-[20px] bg-surface px-4 py-3">
                <p className="text-xs uppercase tracking-[0.18em] text-mist">Next step</p>
                <p className="mt-2 text-sm font-semibold text-ink">
                  {daily?.meals?.length ? "Use pantry intelligence for tonight" : "Scan pantry and reveal next moves"}
                </p>
              </div>
            </div>
            {error ? <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {rings.map((ring) => (
          <MacroRing key={ring.label} {...ring} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="surface-card p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="section-title">7-Day Macro Adherence</h2>
              <p className="muted-copy mt-1">Protein, carbs, fat, and calories rolled into one daily adherence score.</p>
            </div>
          </div>

          <div className="mt-6 h-72">
            {loading ? (
              <div className="flex h-full items-center justify-center text-sm text-mist">Loading chart...</div>
            ) : history.some((point) => point.adherence > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d7e7db" />
                  <XAxis dataKey="date" tick={{ fill: "#6c7c72", fontSize: 12 }} tickLine={false} />
                  <YAxis tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fill: "#6c7c72", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip formatter={(value) => `${Math.round(value * 100)}%`} />
                  <Bar dataKey="adherence" fill="#1a7a4a" radius={[12, 12, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-sand bg-white/70 px-6 text-center text-sm text-mist">
                Your adherence chart will appear after you log meals for a few days.
              </div>
            )}
          </div>
        </div>

        <div className="surface-card p-6">
          <h2 className="section-title">Today&apos;s Activity</h2>
          <p className="muted-copy mt-1">Recent meals and macro progress for the day.</p>

          <div className="mt-6 space-y-3">
            {daily?.meals?.length ? (
              daily.meals.map((meal) => (
                <div key={meal.id} className="rounded-[22px] bg-white/80 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-ink">{meal.recipe_name}</p>
                      <p className="mt-1 text-sm text-mist">
                        {new Date(meal.date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                    <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
                      {Math.round(meal.calories_logged)} kcal
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
                No meals logged today yet. Pick a recommendation and log it from the recipe card.
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.section>
  );
}
