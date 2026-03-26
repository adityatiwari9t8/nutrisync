import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import api, { getErrorMessage } from "../api/api";

function TrendCard({ label, value }) {
  const positive = value >= 0;
  return (
    <div className="rounded-[22px] bg-white/80 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-mist">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${positive ? "text-brand" : "text-orange-600"}`}>
        {positive ? "+" : ""}
        {value}
      </p>
    </div>
  );
}

function SessionStatusBadge({ status }) {
  const normalized = (status || "pending").toLowerCase();
  const className =
    normalized === "confirmed"
      ? "bg-brand/10 text-brand"
      : normalized === "pending"
        ? "bg-amber-100 text-amber-700"
        : "bg-surface text-ink";

  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${className}`}>
      {normalized}
    </span>
  );
}

function DietitianConciergeCard({
  dietitian,
  latestRequest,
  selectedSlot,
  setSelectedSlot,
  goalFocus,
  setGoalFocus,
  notes,
  setNotes,
  requesting,
  requestSuccess,
  onRequestSession,
}) {
  if (!dietitian) {
    return (
      <div className="surface-card p-6 text-sm text-mist">
        Dietitian availability is loading. Refresh in a moment to request a consult.
      </div>
    );
  }

  return (
    <div className="surface-card overflow-hidden p-6 sm:p-8">
      <div className="flex flex-col gap-8 xl:grid xl:grid-cols-[1.05fr_0.95fr]">
        <div>
          <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand">
            Featured dietitian
          </span>
          <h2 className="mt-5 text-3xl font-extrabold tracking-tight text-ink">{dietitian.name}</h2>
          <p className="mt-2 text-sm font-semibold uppercase tracking-[0.2em] text-mist">{dietitian.title}</p>
          <p className="mt-2 text-sm text-mist">{dietitian.credentials}</p>
          <p className="mt-4 max-w-2xl text-base text-mist">{dietitian.bio}</p>

          <div className="mt-5 flex flex-wrap gap-2">
            {dietitian.specialties.map((specialty) => (
              <span key={specialty} className="rounded-full bg-surface px-3 py-2 text-sm font-medium text-ink">
                {specialty}
              </span>
            ))}
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Response window</p>
              <p className="mt-2 text-sm font-medium text-ink">{dietitian.response_time}</p>
            </div>
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Session format</p>
              <p className="mt-2 text-sm font-medium text-ink">{dietitian.session_modes.join(" + ")}</p>
            </div>
          </div>

          {latestRequest ? (
            <div className="mt-6 rounded-[28px] bg-brand/10 p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-ink">Latest session request</p>
                  <p className="mt-2 text-lg font-semibold text-brand">{latestRequest.preferred_slot}</p>
                  <p className="mt-2 text-sm text-mist">Focus: {latestRequest.goal_focus}</p>
                  <p className="mt-2 text-sm text-mist">Format: {latestRequest.session_mode}</p>
                  {latestRequest.notes ? <p className="mt-2 text-sm text-mist">Notes: {latestRequest.notes}</p> : null}
                </div>
                <SessionStatusBadge status={latestRequest.status} />
              </div>
            </div>
          ) : null}
        </div>

        <div className="rounded-[28px] bg-white/75 p-5">
          <p className="text-sm font-semibold text-ink">Request a consult</p>
          <p className="mt-2 text-sm text-mist">
            Choose an opening, share your nutrition focus, and save the request for follow-up.
          </p>

          <div className="mt-5 space-y-2">
            {dietitian.next_openings.map((slot) => {
              const active = selectedSlot === slot;
              return (
                <button
                  key={slot}
                  type="button"
                  onClick={() => setSelectedSlot(slot)}
                  className={`w-full rounded-2xl border px-4 py-3 text-left text-sm transition ${
                    active
                      ? "border-brand bg-brand text-white shadow-soft"
                      : "border-sand bg-white text-ink hover:border-brand/50"
                  }`}
                >
                  {slot}
                </button>
              );
            })}
          </div>

          <label className="mt-5 block space-y-2">
            <span className="text-sm font-medium text-ink">Primary goal</span>
            <input
              type="text"
              value={goalFocus}
              onChange={(event) => setGoalFocus(event.target.value)}
              placeholder="Build a high-protein routine that still feels practical"
              className="input-shell"
            />
          </label>

          <label className="mt-4 block space-y-2">
            <span className="text-sm font-medium text-ink">Notes for the dietitian</span>
            <textarea
              rows="4"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Share schedule constraints, food preferences, or coaching goals."
              className="input-shell min-h-28 resize-y"
            />
          </label>

          <button type="button" onClick={onRequestSession} disabled={requesting || !selectedSlot} className="primary-button mt-6 w-full">
            {requesting ? "Confirming session..." : latestRequest ? "Update Session Request" : "Request Dietitian Session"}
          </button>

          {requestSuccess ? (
            <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{requestSuccess}</p>
          ) : (
            <p className="mt-4 text-sm text-mist">
              Your request is saved to your account so you can revisit the selected time later.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DietitianPortal() {
  const [dashboard, setDashboard] = useState(null);
  const [dietitian, setDietitian] = useState(null);
  const [latestRequest, setLatestRequest] = useState(null);
  const [paywalled, setPaywalled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSlot, setSelectedSlot] = useState("");
  const [goalFocus, setGoalFocus] = useState("Macro alignment and practical meal planning");
  const [notes, setNotes] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState("");

  useEffect(() => {
    const loadPortal = async () => {
      setLoading(true);
      setError("");
      setPaywalled(false);

      const [conciergeResult, dashboardResult] = await Promise.allSettled([
        api.get("/dietitian/concierge"),
        api.get("/dietitian/dashboard"),
      ]);

      if (conciergeResult.status === "fulfilled") {
        const concierge = conciergeResult.value.data;
        setDietitian(concierge.dietitian);
        setLatestRequest(concierge.latest_request);
        setSelectedSlot(concierge.latest_request?.preferred_slot || concierge.dietitian?.next_openings?.[0] || "");
        if (concierge.latest_request?.goal_focus) {
          setGoalFocus(concierge.latest_request.goal_focus);
        }
        if (concierge.latest_request?.notes) {
          setNotes(concierge.latest_request.notes);
        }
      } else {
        setError(getErrorMessage(conciergeResult.reason, "Unable to load dietitian availability."));
      }

      if (dashboardResult.status === "fulfilled") {
        setDashboard(dashboardResult.value.data);
      } else if (dashboardResult.reason?.response?.status === 403) {
        setPaywalled(true);
        setDashboard(null);
      } else {
        setDashboard(null);
        setError(getErrorMessage(dashboardResult.reason, "Unable to load the dietitian portal."));
      }

      setLoading(false);
    };

    loadPortal();
  }, []);

  const handleRequestSession = async () => {
    const preferredSlot = selectedSlot || dietitian?.next_openings?.[0] || "";
    if (!preferredSlot) {
      return;
    }

    setRequesting(true);
    setError("");
    setRequestSuccess("");

    try {
      const { data } = await api.post("/dietitian/request-session", {
        preferred_slot: preferredSlot,
        goal_focus: goalFocus,
        notes,
      });
      setLatestRequest(data);
      setSelectedSlot(data.preferred_slot);
      setGoalFocus(data.goal_focus);
      setNotes(data.notes);
      setRequestSuccess(`Session confirmed with ${data.dietitian_name} for ${data.preferred_slot}.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to request a dietitian session."));
    } finally {
      setRequesting(false);
    }
  };

  if (loading) {
    return (
      <section className="page-shell">
        <div className="surface-card p-10 text-center text-sm text-mist">Loading dietitian portal...</div>
      </section>
    );
  }

  if (paywalled) {
    return (
      <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
        <div className="surface-card overflow-hidden p-8 sm:p-10">
          <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand">
            Premium insights
          </span>
          <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-ink">Unlock consultation-ready nutrition insights.</h1>
          <p className="mt-4 max-w-2xl text-base text-mist">
            Premium gives you longer-range adherence trends, day-by-day nutrition history, and a
            cleaner picture of how your routine is evolving over time.
          </p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">14-day history for review and pattern spotting.</div>
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">Average intake summaries across the core macro categories.</div>
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">Trend cards that highlight where habits are improving or drifting.</div>
          </div>
        </div>

        {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}

        <DietitianConciergeCard
          dietitian={dietitian}
          latestRequest={latestRequest}
          selectedSlot={selectedSlot}
          setSelectedSlot={setSelectedSlot}
          goalFocus={goalFocus}
          setGoalFocus={setGoalFocus}
          notes={notes}
          setNotes={setNotes}
          requesting={requesting}
          requestSuccess={requestSuccess}
          onRequestSession={handleRequestSession}
        />
      </motion.section>
    );
  }

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Dietitian portal</h1>
        <p className="mt-3 text-base text-mist">
          Review long-range averages, trend direction, and detailed daily nutrition history.
        </p>
        {error ? <p className="mt-6 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="surface-card p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-mist">Avg protein</p>
          <p className="mt-2 text-3xl font-bold text-ink">{dashboard?.averages?.protein}g</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-mist">Avg carbs</p>
          <p className="mt-2 text-3xl font-bold text-ink">{dashboard?.averages?.carbs}g</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-mist">Avg fat</p>
          <p className="mt-2 text-3xl font-bold text-ink">{dashboard?.averages?.fat}g</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-mist">Avg calories</p>
          <p className="mt-2 text-3xl font-bold text-ink">{dashboard?.averages?.calories}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <TrendCard label="Protein trend" value={dashboard?.trends?.protein_trend || 0} />
        <TrendCard label="Carbs trend" value={dashboard?.trends?.carbs_trend || 0} />
        <TrendCard label="Fat trend" value={dashboard?.trends?.fat_trend || 0} />
        <TrendCard label="Calorie trend" value={dashboard?.trends?.calorie_trend || 0} />
      </div>

      <DietitianConciergeCard
        dietitian={dietitian}
        latestRequest={latestRequest}
        selectedSlot={selectedSlot}
        setSelectedSlot={setSelectedSlot}
        goalFocus={goalFocus}
        setGoalFocus={setGoalFocus}
        notes={notes}
        setNotes={setNotes}
        requesting={requesting}
        requestSuccess={requestSuccess}
        onRequestSession={handleRequestSession}
      />

      <div className="surface-card p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="section-title">Nutritional history</h2>
            <p className="muted-copy mt-1">Fourteen days of daily totals and adherence.</p>
          </div>
        </div>

        {dashboard?.meals?.length ? (
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full overflow-hidden rounded-[22px] bg-white/80 text-left">
              <thead className="bg-surface text-sm text-mist">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Protein</th>
                  <th className="px-4 py-3 font-medium">Carbs</th>
                  <th className="px-4 py-3 font-medium">Fat</th>
                  <th className="px-4 py-3 font-medium">Calories</th>
                  <th className="px-4 py-3 font-medium">Adherence</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.meals.map((row) => (
                  <tr key={row.date} className="border-t border-sand/80 text-sm text-ink">
                    <td className="px-4 py-3">{row.date}</td>
                    <td className="px-4 py-3">{row.protein}g</td>
                    <td className="px-4 py-3">{row.carbs}g</td>
                    <td className="px-4 py-3">{row.fat}g</td>
                    <td className="px-4 py-3">{row.calories}</td>
                    <td className="px-4 py-3">{Math.round(row.adherence * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-6 rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
            Once a few days of logs are available, this table becomes a concise review sheet for coaching and follow-up.
          </div>
        )}
      </div>
    </motion.section>
  );
}
