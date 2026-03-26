import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage, getStoredUser, storeAuth } from "../api/api";

export default function Login({ onAuthSuccess }) {
  const navigate = useNavigate();
  const existingUser = getStoredUser();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (existingUser) {
    return <Navigate to="/" replace />;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", form);
      storeAuth(data);
      onAuthSuccess();
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to sign you in."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="page-shell flex min-h-screen items-center justify-center"
    >
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="surface-card overflow-hidden p-8 sm:p-10">
          <div className="max-w-md">
            <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand">
              Personalized nutrition planning
            </span>
            <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-ink sm:text-5xl">
              Turn pantry snapshots into meals that fit your macros.
            </h1>
            <p className="mt-4 text-base text-mist">
              NutriSync helps you discover meals around what you already have, with nutrition data,
              macro targets, and pantry-aware recommendations working together behind the scenes.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <div className="rounded-[22px] bg-white/75 p-4">
                <p className="text-sm font-semibold text-ink">Scan faster</p>
                <p className="mt-2 text-xs leading-5 text-mist">Capture ingredients from a single fridge or shelf photo.</p>
              </div>
              <div className="rounded-[22px] bg-white/75 p-4">
                <p className="text-sm font-semibold text-ink">Match smarter</p>
                <p className="mt-2 text-xs leading-5 text-mist">Get meals ranked around fit, preference, and pantry usage.</p>
              </div>
              <div className="rounded-[22px] bg-white/75 p-4">
                <p className="text-sm font-semibold text-ink">Track daily</p>
                <p className="mt-2 text-xs leading-5 text-mist">See whether each meal keeps you on pace for the day.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="surface-card p-8 sm:p-10">
          <h2 className="text-2xl font-bold tracking-tight text-ink">Welcome back</h2>
          <p className="mt-2 text-sm text-mist">Sign in to continue your meal plan and macro tracking.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Email address"
              className="input-shell"
              required
            />
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Password"
              className="input-shell"
              required
            />

            {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}

            <button type="submit" disabled={loading} className="primary-button w-full">
              {loading ? "Signing in..." : "Login"}
            </button>
          </form>

          <p className="mt-6 text-sm text-mist">
            Need an account?{" "}
            <Link to="/register" className="font-semibold text-brand">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </motion.section>
  );
}
