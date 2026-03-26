import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage, getStoredUser, storeAuth } from "../api/api";

export default function Register({ onAuthSuccess }) {
  const navigate = useNavigate();
  const existingUser = getStoredUser();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    is_premium: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (existingUser) {
    return <Navigate to="/" replace />;
  }

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/register", {
        ...form,
        is_premium: false,
      });
      storeAuth(data);
      onAuthSuccess();
      navigate(form.is_premium ? "/upgrade/premium" : "/", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to create your account."));
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
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="surface-card p-8 sm:p-10">
          <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand">
            Guided account setup
          </span>
          <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-ink">Create your NutriSync profile</h1>
          <p className="mt-4 text-base text-mist">
            Set up your account once and keep every pantry scan, recommendation, and macro target
            in sync across your planning flow.
          </p>
          <div className="mt-8 space-y-3">
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">
              Pantry scans help you start from what is already available at home.
            </div>
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">
              Daily tracking shows whether each meal moves you closer to your goals.
            </div>
            <div className="rounded-[22px] bg-white/75 p-4 text-sm text-mist">
              Premium unlocks longer-range history and nutrition reporting built for coaching conversations.
            </div>
          </div>
        </div>

        <div className="surface-card p-8 sm:p-10">
          <h2 className="text-2xl font-bold tracking-tight text-ink">Register</h2>
          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Username"
              className="input-shell"
              required
            />
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

            <label className="flex items-start gap-3 rounded-2xl border border-sand bg-white/80 p-4 text-sm text-ink">
              <input
                type="checkbox"
                name="is_premium"
                checked={form.is_premium}
                onChange={handleChange}
                className="mt-1 h-4 w-4 accent-brand"
              />
              <span>
                <strong>Include Premium insights</strong>
                <br />
                Unlock advanced trend analysis, averages, and full nutrition history.
                <br />
                <span className="text-mist">You will review payment on the next step.</span>
              </span>
            </label>

            {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}

            <button type="submit" disabled={loading} className="primary-button w-full">
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-sm text-mist">
            Already a member?{" "}
            <Link to="/login" className="font-semibold text-brand">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </motion.section>
  );
}
