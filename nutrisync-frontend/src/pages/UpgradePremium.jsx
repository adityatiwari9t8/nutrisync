import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import api, { getErrorMessage, storeAuth } from "../api/api";

const paymentMethods = [
  {
    id: "card",
    label: "Credit or debit card",
    note: "Visa, Mastercard, and AmEx accepted",
  },
  {
    id: "apple_pay",
    label: "Apple Pay",
    note: "Sandbox wallet flow on supported devices",
  },
  {
    id: "upi",
    label: "UPI",
    note: "Instant bank transfer and wallet flow",
  },
];

function BenefitRow({ title, copy }) {
  return (
    <div className="rounded-[22px] bg-white/75 p-4">
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-mist">{copy}</p>
    </div>
  );
}

export default function UpgradePremium({ user, onAuthSuccess }) {
  const navigate = useNavigate();
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [cardholderName, setCardholderName] = useState(user?.username || "");
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");
  const [upiId, setUpiId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpgrade = async (event) => {
    event.preventDefault();
    setError("");

    if (paymentMethod === "card") {
      const digits = cardNumber.replace(/\D/g, "");
      if (!cardholderName.trim() || digits.length < 12 || expiry.trim().length < 4 || cvv.trim().length < 3) {
        setError("Enter valid card details to continue.");
        return;
      }
    }

    if (paymentMethod === "upi" && !upiId.includes("@")) {
      setError("Enter a valid UPI ID to continue.");
      return;
    }

    setLoading(true);

    try {
      const { data } = await api.post("/auth/upgrade", {
        billing_cycle: "monthly",
        payment_method: paymentMethod,
        cardholder_name: cardholderName.trim(),
        card_last4: paymentMethod === "card" ? cardNumber.replace(/\D/g, "").slice(-4) : "",
      });
      storeAuth(data);
      onAuthSuccess?.();
      navigate("/dietitian", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to complete the premium upgrade right now."));
    } finally {
      setLoading(false);
    }
  };

  if (user?.is_premium) {
    return (
      <section className="page-shell">
        <div className="surface-card p-8 text-center sm:p-10">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink">Premium already active</h1>
          <p className="mt-4 text-base text-mist">
            Your account already has Premium access. You can head straight back into the Dietitian portal.
          </p>
          <button type="button" onClick={() => navigate("/dietitian")} className="primary-button mt-8">
            Open Dietitian Portal
          </button>
        </div>
      </section>
    );
  }

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Premium access checkout</p>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
          Review the premium plan and activate access through the sandbox checkout flow.
        </h1>
        <p className="mt-4 max-w-3xl text-base text-mist">
          This screen supports local premium activation for development and portfolio review. It
          unlocks the premium experience inside NutriSync without sending a live payment request.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.95fr]">
        <div className="surface-card p-6 sm:p-8">
          <div className="rounded-[30px] bg-brand px-6 py-7 text-white shadow-[0_20px_45px_rgba(26,122,74,0.2)]">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-white/75">Premium plan</p>
            <div className="mt-4 flex items-end gap-3">
              <p className="text-5xl font-extrabold tracking-tight">$9.99</p>
              <p className="pb-2 text-lg text-white/80">per month</p>
            </div>
            <p className="mt-4 max-w-lg text-sm text-white/80">
              Includes expanded nutrition history, premium portal access, and the session request workflow.
            </p>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <BenefitRow title="Advanced macro trends" copy="See longer-range adherence shifts and averages across your full history." />
            <BenefitRow title="Dietitian portal" copy="Open the premium-only portal with trend views, history, and coaching context." />
            <BenefitRow title="Consult booking" copy="Request and manage 1-on-1 sessions from inside the product." />
            <BenefitRow title="Sandbox activation" copy="Completing this flow upgrades the account in the local environment immediately." />
          </div>
        </div>

        <form onSubmit={handleUpgrade} className="surface-card p-6 sm:p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-ink">Choose a payment option</p>
              <p className="mt-1 text-sm text-mist">Select the method you want to use for the monthly plan.</p>
            </div>
            <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">Sandbox checkout</span>
          </div>

          <div className="mt-6 space-y-3">
            {paymentMethods.map((method) => {
              const active = paymentMethod === method.id;
              return (
                <button
                  key={method.id}
                  type="button"
                  onClick={() => setPaymentMethod(method.id)}
                  className={`w-full rounded-[22px] border px-4 py-4 text-left transition ${
                    active
                      ? "border-brand bg-brand/5 shadow-soft"
                      : "border-sand bg-white/70 hover:border-brand/40"
                  }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-ink">{method.label}</p>
                      <p className="mt-1 text-sm text-mist">{method.note}</p>
                    </div>
                    <span className={`h-5 w-5 rounded-full border-2 ${active ? "border-brand bg-brand" : "border-sand bg-white"}`} />
                  </div>
                </button>
              );
            })}
          </div>

          {paymentMethod === "card" ? (
            <div className="mt-6 space-y-4">
              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">Cardholder name</span>
                <input
                  type="text"
                  value={cardholderName}
                  onChange={(event) => setCardholderName(event.target.value)}
                  placeholder="Aditya Tiwari"
                  className="input-shell"
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">Card number</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={cardNumber}
                  onChange={(event) => setCardNumber(event.target.value)}
                  placeholder="4242 4242 4242 4242"
                  className="input-shell"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">Expiry</span>
                  <input
                    type="text"
                    value={expiry}
                    onChange={(event) => setExpiry(event.target.value)}
                    placeholder="08/28"
                    className="input-shell"
                  />
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">CVV</span>
                  <input
                    type="password"
                    inputMode="numeric"
                    value={cvv}
                    onChange={(event) => setCvv(event.target.value)}
                    placeholder="123"
                    className="input-shell"
                  />
                </label>
              </div>
            </div>
          ) : null}

          {paymentMethod === "upi" ? (
            <label className="mt-6 block space-y-2">
              <span className="text-sm font-medium text-ink">UPI ID</span>
              <input
                type="text"
                value={upiId}
                onChange={(event) => setUpiId(event.target.value)}
                placeholder="name@bank"
                className="input-shell"
              />
            </label>
          ) : null}

          {paymentMethod === "apple_pay" ? (
            <div className="mt-6 rounded-[22px] bg-white/80 p-4 text-sm text-mist">
              Apple Pay is presented here as a sandbox option for the local product flow.
            </div>
          ) : null}

          {error ? <p className="mt-5 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}

          <div className="mt-5 rounded-[22px] border border-brand/10 bg-brand/5 p-4 text-sm text-mist">
            No live payment is processed on this screen. It records a local sandbox checkout and unlocks the premium experience in this environment.
          </div>

          <div className="mt-8 rounded-[24px] bg-surface/80 p-4">
            <div className="flex items-center justify-between text-sm text-mist">
              <span>Premium monthly</span>
              <span>$9.99</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-base font-semibold text-ink">
              <span>Total due today</span>
              <span>$9.99</span>
            </div>
          </div>

          <button type="submit" disabled={loading} className="primary-button mt-8 w-full py-4 text-base">
            {loading ? "Completing sandbox checkout..." : "Complete Sandbox Checkout"}
          </button>

          <button type="button" onClick={() => navigate("/dietitian")} className="secondary-button mt-3 w-full">
            Back to Dietitian Page
          </button>
        </form>
      </div>
    </motion.section>
  );
}
