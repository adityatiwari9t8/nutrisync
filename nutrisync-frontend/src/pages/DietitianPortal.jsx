import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

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

function PremiumDietitianIllustration() {
  return (
    <div className="mx-auto w-full max-w-[360px] rounded-[32px] border border-white/80 bg-white/90 p-5 shadow-[0_24px_60px_rgba(18,53,36,0.08)]">
      <svg viewBox="0 0 420 220" className="h-auto w-full" role="img" aria-label="Dietitian consultation illustration">
        <rect x="0" y="0" width="420" height="220" rx="28" fill="#FCFEFC" />
        <rect x="24" y="30" width="70" height="70" rx="18" fill="#E6EFE7" />
        <rect x="332" y="116" width="56" height="56" rx="16" fill="#E6EFE7" />
        <circle cx="372" cy="44" r="14" fill="#1A7A4A" />
        <circle cx="38" cy="180" r="10" fill="#1A7A4A" fillOpacity="0.9" />
        <circle cx="390" cy="66" r="6" fill="#1A7A4A" fillOpacity="0.5" />
        <rect x="132" y="104" width="154" height="10" rx="5" fill="#B8C6BC" />
        <rect x="150" y="114" width="10" height="56" rx="5" fill="#B8C6BC" />
        <rect x="256" y="114" width="10" height="56" rx="5" fill="#B8C6BC" />
        <rect x="172" y="88" width="26" height="28" rx="8" fill="#EDF3EC" />
        <path d="M185 116V72" stroke="#B8C6BC" strokeWidth="4" strokeLinecap="round" />
        <path d="M185 72c12 2 18 10 18 22-11 0-18-5-18-14 0-3 0-5 0-8Z" fill="#1A7A4A" fillOpacity="0.9" />
        <path d="M185 86c-10-8-16-10-26-10 2 15 10 24 26 24" fill="#6FB38B" fillOpacity="0.9" />
        <path d="M185 82c8-7 14-8 22-8-1 11-8 18-22 18" fill="#9BC8AA" />
        <circle cx="118" cy="92" r="18" fill="#E5E7EB" />
        <rect x="97" y="112" width="42" height="52" rx="18" fill="#1F513A" />
        <path d="M97 136c9 6 18 9 28 9 5 0 10-1 14-3" stroke="#F7F9F7" strokeWidth="3" strokeLinecap="round" />
        <path d="M136 126l34 -8" stroke="#1F513A" strokeWidth="4" strokeLinecap="round" />
        <circle cx="300" cy="92" r="18" fill="#E5E7EB" />
        <rect x="279" y="112" width="42" height="52" rx="18" fill="#D9D6D1" />
        <path d="M279 136c9 6 18 9 28 9 5 0 10-1 14-3" stroke="#6D6B67" strokeWidth="3" strokeLinecap="round" />
        <path d="M284 126l-28 -4" stroke="#6D6B67" strokeWidth="4" strokeLinecap="round" />
        <path d="M250 110c8 6 15 11 21 15" stroke="#6D6B67" strokeWidth="3" strokeLinecap="round" />
      </svg>
    </div>
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
  const navigate = useNavigate();
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
      setDashboard(null);
      setDietitian(null);
      setLatestRequest(null);
      setSelectedSlot("");
      setGoalFocus("Macro alignment and practical meal planning");
      setNotes("");
      setRequestSuccess("");

      try {
        const { data: dashboardData } = await api.get("/dietitian/dashboard");
        setDashboard(dashboardData);

        try {
          const { data: concierge } = await api.get("/dietitian/concierge");
          setDietitian(concierge.dietitian);
          setLatestRequest(concierge.latest_request);
          setSelectedSlot(concierge.latest_request?.preferred_slot || concierge.dietitian?.next_openings?.[0] || "");
          if (concierge.latest_request?.goal_focus) {
            setGoalFocus(concierge.latest_request.goal_focus);
          }
          if (concierge.latest_request?.notes) {
            setNotes(concierge.latest_request.notes);
          }
        } catch (conciergeError) {
          setError(getErrorMessage(conciergeError, "Unable to load dietitian availability."));
        }
      } catch (dashboardError) {
        if (dashboardError?.response?.status === 403) {
          setPaywalled(true);
        } else {
          setError(getErrorMessage(dashboardError, "Unable to load the dietitian portal."));
        }
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
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="page-shell flex min-h-[calc(100vh-140px)] items-center justify-center py-6"
      >
        <div className="surface-card w-full max-w-5xl overflow-hidden border-white/90 bg-white/70 px-6 py-10 text-center shadow-[0_32px_80px_rgba(18,53,36,0.12)] sm:px-10 sm:py-14">
          <PremiumDietitianIllustration />

          <div className="mx-auto mt-10 flex h-16 w-16 items-center justify-center rounded-full border border-[#F4E7B6] bg-[#FFF8DE] shadow-[0_12px_28px_rgba(212,166,30,0.16)]">
            <svg viewBox="0 0 24 24" className="h-7 w-7 text-[#C98500]" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="5" y="10" width="14" height="10" rx="2" />
              <path d="M8 10V8a4 4 0 0 1 8 0v2" />
            </svg>
          </div>

          <h1 className="mt-7 text-4xl font-extrabold tracking-tight text-ink sm:text-5xl">
            Unlock the Dietitian Portal
          </h1>
          <p className="mx-auto mt-5 max-w-3xl text-lg leading-9 text-mist">
            Upgrade to Premium to share your macro history directly with certified professionals,
            get advanced trends, and book 1-on-1 consultations.
          </p>

          <button
            type="button"
            onClick={() => navigate("/upgrade/premium")}
            className="mx-auto mt-10 inline-flex w-full max-w-[420px] items-center justify-center rounded-[20px] bg-brand px-8 py-5 text-xl font-semibold text-white shadow-[0_20px_45px_rgba(26,122,74,0.28)] transition hover:brightness-110"
          >
            Upgrade to Premium — $9.99/mo
          </button>

          {error ? <p className="mx-auto mt-6 max-w-2xl rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
        </div>
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
