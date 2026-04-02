import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage } from "../api/api";
import IngredientTag from "../components/IngredientTag";

const defaultGoals = { protein: 140, carbs: 180, fat: 55, calories: 2100 };

function InsightMetricCard({ label, value, caption }) {
  return (
    <div className="rounded-[26px] border border-white/80 bg-white/80 p-5 shadow-[0_18px_40px_rgba(18,53,36,0.06)]">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-mist">{label}</p>
      <p className="mt-3 text-3xl font-black tracking-tight text-ink">{value}</p>
      <p className="mt-2 text-sm text-mist">{caption}</p>
    </div>
  );
}

function ZoneCard({ zone }) {
  const tone = {
    strong: "border-emerald-200 bg-emerald-50/90 text-emerald-800",
    building: "border-brand/15 bg-brand/5 text-ink",
    missing: "border-sand bg-white/85 text-ink",
  }[zone.status] || "border-sand bg-white/85 text-ink";

  return (
    <div className={`rounded-[24px] border p-4 ${tone}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{zone.label}</p>
          <p className="mt-2 text-sm leading-6 opacity-80">{zone.description}</p>
        </div>
        <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold shadow-sm">{zone.count}</span>
      </div>
      {zone.examples?.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {zone.examples.map((example) => (
            <span key={example} className="rounded-full bg-white/90 px-3 py-1 text-xs font-medium text-ink shadow-sm">
              {example}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function UnlockSuggestion({ suggestion }) {
  return (
    <div className="rounded-[22px] bg-white/80 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">{suggestion.ingredient}</p>
          <p className="mt-1 text-sm text-mist">
            Could unlock {suggestion.unlock_count} stronger recipe path{suggestion.unlock_count === 1 ? "" : "s"}.
          </p>
        </div>
        <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
          +{suggestion.unlock_count}
        </span>
      </div>
      {suggestion.recipe_examples?.length ? (
        <p className="mt-3 text-xs uppercase tracking-[0.16em] text-mist">
          Opens into {suggestion.recipe_examples.join(" and ")}
        </p>
      ) : null}
    </div>
  );
}

function SpotlightRecipeCard({ recipe, onView }) {
  return (
    <div className="overflow-hidden rounded-[26px] border border-white/80 bg-white/80 shadow-[0_18px_45px_rgba(18,53,36,0.07)]">
      <div className="bg-gradient-to-br from-brand/95 via-brand to-emerald-400 p-5 text-white">
        <div className="flex items-start justify-between gap-4">
          <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur">
            {recipe.cuisine}
          </span>
          <span className="rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-brand">
            {Math.round(recipe.match_score * 100)}% pantry fit
          </span>
        </div>
        <h3 className="mt-5 text-2xl font-bold tracking-tight">{recipe.name}</h3>
        <p className="mt-2 text-sm text-white/80">{recipe.readiness_label}</p>
      </div>

      <div className="space-y-4 p-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-mist">Already covered</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {recipe.matched_ingredients.map((ingredient) => (
              <span key={ingredient} className="rounded-full bg-brand/10 px-3 py-1 text-xs font-medium text-brand">
                {ingredient}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-mist">Still missing</p>
          {recipe.missing_ingredients?.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {recipe.missing_ingredients.map((ingredient) => (
                <span key={ingredient} className="rounded-full bg-surface px-3 py-1 text-xs font-medium text-ink">
                  {ingredient}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-mist">No major gaps detected.</p>
          )}
        </div>

        <button type="button" onClick={onView} className="secondary-button w-full">
          View Recipe
        </button>
      </div>
    </div>
  );
}

export default function PantryScan() {
  const navigate = useNavigate();
  const [ingredients, setIngredients] = useState([]);
  const [goals, setGoals] = useState(defaultGoals);
  const [manualIngredient, setManualIngredient] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [syncingPantry, setSyncingPantry] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [insights, setInsights] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const uploadInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const cameraInputRef = useRef(null);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraOpen(false);
  };

  const loadInsights = async (showLoader = true) => {
    if (showLoader) {
      setInsightsLoading(true);
    }
    try {
      const { data } = await api.get("/pantry/insights");
      setInsights(data);
    } catch {
      // The pantry UI still works without the intelligence layer.
    } finally {
      if (showLoader) {
        setInsightsLoading(false);
      }
    }
  };

  useEffect(() => {
    const loadPantry = async () => {
      try {
        const [pantryResponse, dailyResponse, insightsResponse] = await Promise.all([
          api.get("/pantry/ingredients"),
          api.get("/tracker/daily"),
          api.get("/pantry/insights"),
        ]);
        setIngredients(pantryResponse.data.ingredients || []);
        setInsights(insightsResponse.data);
        if (dailyResponse.data?.goals) {
          const nextGoals = dailyResponse.data.goals;
          if (Object.values(nextGoals).some((value) => value > 0)) {
            setGoals(nextGoals);
          }
        }
      } catch {
        // The empty state is fine here.
      } finally {
        setInsightsLoading(false);
      }
    };

    loadPantry();

    return () => {
      stopCamera();
    };
  }, []);

  const persistIngredients = async (nextIngredients, successMessage) => {
    setSyncingPantry(true);
    setError("");
    try {
      const { data } = await api.put("/pantry/ingredients", { ingredients: nextIngredients });
      setIngredients(data.ingredients || []);
      setStatus(successMessage);
      await loadInsights(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to update your pantry right now."));
    } finally {
      setSyncingPantry(false);
    }
  };

  const uploadImage = async (file) => {
    if (!file?.type?.startsWith("image/")) {
      setError("Please choose an image file to scan.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");
    setStatus("");
    setCameraError("");
    try {
      const { data } = await api.post("/pantry/scan", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setIngredients(data.ingredients || []);
      setStatus("Scan complete. Pantry intelligence refreshed below.");
      await loadInsights(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to scan that image right now."));
    } finally {
      setLoading(false);
    }
  };

  const startCamera = async () => {
    setCameraError("");
    setError("");

    if (!navigator.mediaDevices?.getUserMedia) {
      if (cameraInputRef.current) {
        cameraInputRef.current.value = "";
      }
      cameraInputRef.current?.click();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });

      streamRef.current = stream;
      setCameraOpen(true);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
    } catch {
      setCameraError("Camera access is unavailable right now. You can still upload a photo instead.");
    }
  };

  const captureFromCamera = async () => {
    if (!videoRef.current) {
      return;
    }

    const video = videoRef.current;
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("We could not capture the camera frame. Please try again.");
      return;
    }

    context.drawImage(video, 0, 0, width, height);

    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.92);
    });

    if (!blob) {
      setCameraError("We could not create a scan image. Please try again.");
      return;
    }

    stopCamera();
    await uploadImage(new File([blob], `pantry-scan-${Date.now()}.jpg`, { type: "image/jpeg" }));
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      await uploadImage(file);
    }
  };

  const handleManualAdd = async () => {
    const normalized = manualIngredient.trim().toLowerCase();
    if (!normalized || ingredients.includes(normalized)) {
      setManualIngredient("");
      return;
    }
    setManualIngredient("");
    await persistIngredients([...ingredients, normalized], `${normalized} added to your pantry.`);
  };

  const handleGoalChange = (event) => {
    const { name, value } = event.target;
    setGoals((current) => ({ ...current, [name]: Number(value) }));
  };

  const handleFindRecipes = () => {
    navigate("/recipes", { state: { ingredients, macroGoals: goals } });
  };

  const strongestZone = insights?.zones?.length
    ? [...insights.zones].sort((left, right) => right.count - left.count)[0]
    : null;

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Ingredient detection + pantry intelligence</p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Scan your kitchen, then plan the smartest next move</h1>
            <p className="mt-4 text-base text-mist">
              NutriSync now does more than detect ingredients. It tells you how balanced your pantry feels,
              what recipes are close, and which single ingredient would unlock the most momentum.
            </p>
          </div>

          <div className="rounded-[30px] bg-white/75 p-5">
            <p className="text-sm font-semibold text-ink">What makes this different</p>
            <div className="mt-4 space-y-3 text-sm text-mist">
              <p>1. Scan or upload a real kitchen photo.</p>
              <p>2. Clean up the pantry list with persistent manual edits.</p>
              <p>3. Let NutriSync show your pantry score, strong zones, unlock ingredients, and tonight&apos;s best recipe paths.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.02fr_0.98fr]">
        <div className="surface-card p-6">
          <div
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`rounded-[28px] border-2 border-dashed p-8 text-center transition ${
              dragActive ? "border-brand bg-brand/5" : "border-sand bg-white/60"
            }`}
          >
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-brand/10 text-2xl text-brand">
              +
            </div>
            <h2 className="mt-5 text-xl font-semibold text-ink">Scan live or add a photo</h2>
            <p className="mt-2 text-sm text-mist">
              Open the camera for a live scan, or upload a fridge, shelf, countertop, or plated-meal image with ingredients clearly visible.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <label className="secondary-button cursor-pointer">
                Upload Photo
                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onClick={(event) => {
                    event.currentTarget.value = "";
                  }}
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      await uploadImage(file);
                    }
                  }}
                />
              </label>
              <button type="button" onClick={startCamera} disabled={loading} className="primary-button">
                Open Camera
              </button>
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onClick={(event) => {
                  event.currentTarget.value = "";
                }}
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    await uploadImage(file);
                  }
                }}
              />
            </div>
            {loading ? <p className="mt-4 text-sm font-medium text-brand">Scanning ingredients...</p> : null}
            {syncingPantry ? <p className="mt-4 text-sm font-medium text-brand">Syncing pantry updates...</p> : null}
            {status ? <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{status}</p> : null}
            {error ? <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
            {cameraError ? <p className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-700">{cameraError}</p> : null}
          </div>

          {cameraOpen ? (
            <div className="mt-5 rounded-[28px] bg-white/75 p-5">
              <div className="flex flex-col gap-4">
                <div className="overflow-hidden rounded-[24px] bg-ink">
                  <video ref={videoRef} playsInline muted className="h-72 w-full object-cover" />
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <button type="button" onClick={captureFromCamera} disabled={loading} className="primary-button">
                    Capture and Scan
                  </button>
                  <button type="button" onClick={stopCamera} className="secondary-button">
                    Cancel Camera
                  </button>
                </div>
                <p className="text-sm text-mist">
                  Point the camera at your food or pantry items, then capture a frame to start the scan.
                </p>
              </div>
            </div>
          ) : null}

          <div className="mt-6">
            <div className="flex flex-wrap gap-2">
              {ingredients.length ? (
                ingredients.map((ingredient) => (
                  <IngredientTag
                    key={ingredient}
                    label={ingredient}
                    onRemove={() =>
                      persistIngredients(
                        ingredients.filter((item) => item !== ingredient),
                        `${ingredient} removed from your pantry.`,
                      )
                    }
                  />
                ))
              ) : (
                <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
                  No ingredients yet. Scan with the camera, upload a photo, or add items manually.
                </div>
              )}
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <input
                type="text"
                value={manualIngredient}
                onChange={(event) => setManualIngredient(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    handleManualAdd();
                  }
                }}
                placeholder="Add ingredient manually"
                className="input-shell"
              />
              <button type="button" onClick={handleManualAdd} disabled={syncingPantry} className="secondary-button sm:min-w-40">
                Add Ingredient
              </button>
            </div>
          </div>
        </div>

        <div className="surface-card p-6">
          <h2 className="section-title">Macro Goals</h2>
          <p className="muted-copy mt-1">These targets are reused to score meal fit across recommendations and tracking.</p>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">Protein (g)</span>
              <input type="number" min="0" name="protein" value={goals.protein} onChange={handleGoalChange} className="input-shell" />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">Carbs (g)</span>
              <input type="number" min="0" name="carbs" value={goals.carbs} onChange={handleGoalChange} className="input-shell" />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">Fat (g)</span>
              <input type="number" min="0" name="fat" value={goals.fat} onChange={handleGoalChange} className="input-shell" />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">Calories (kcal)</span>
              <input type="number" min="0" name="calories" value={goals.calories} onChange={handleGoalChange} className="input-shell" />
            </label>
          </div>

          <div className="mt-8 rounded-[28px] bg-white/80 p-5">
            <p className="text-sm font-semibold text-ink">Why this page matters now</p>
            <p className="mt-2 text-sm text-mist">
              The pantry list below is now a live planning workspace. Manual changes persist, your pantry
              gets scored, and the recipe engine can explain what one extra item would unlock.
            </p>
          </div>

          <button type="button" disabled={!ingredients.length || syncingPantry} onClick={handleFindRecipes} className="primary-button mt-8 w-full">
            Generate Recommendations
          </button>
        </div>
      </div>

      <div className="surface-card overflow-hidden p-6 sm:p-8">
        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[32px] bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.18),transparent_35%),linear-gradient(135deg,#123524_0%,#1a7a4a_55%,#58c68c_100%)] p-6 text-white shadow-[0_28px_70px_rgba(18,53,36,0.18)] sm:p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-white/70">Pantry intelligence</p>
            <div className="mt-5 flex items-end gap-4">
              <p className="text-6xl font-black leading-none tracking-tight">
                {insightsLoading ? "..." : insights?.pantry_score ?? 0}
              </p>
              <div className="pb-1">
                <p className="text-xl font-semibold">{insights?.score_label || "Starter"}</p>
                <p className="mt-1 text-sm text-white/75">kitchen momentum</p>
              </div>
            </div>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-white/80">
              {insights?.summary ||
                "Scan or add ingredients to see what your pantry is good at, what recipes are close, and what single ingredient would unlock more."}
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur">
                {insights?.ingredient_count ?? 0} tracked ingredients
              </span>
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur">
                {insights?.ready_recipe_count ?? 0} recipes within 2 missing items
              </span>
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur">
                {insights?.next_up_recipe_count ?? 0} more after one quick top-up
              </span>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <button type="button" onClick={handleFindRecipes} disabled={!ingredients.length} className="rounded-full bg-white px-5 py-3 text-sm font-semibold text-ink transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60">
                See Full Recommendations
              </button>
              <button type="button" onClick={() => loadInsights(true)} className="rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/15">
                Refresh Intelligence
              </button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <InsightMetricCard
              label="Tracked now"
              value={insightsLoading ? "..." : insights?.ingredient_count ?? 0}
              caption="Everything currently saved in your pantry profile."
            />
            <InsightMetricCard
              label="Tonight-ready"
              value={insightsLoading ? "..." : insights?.ready_recipe_count ?? 0}
              caption="Recipes with two or fewer missing ingredients."
            />
            <InsightMetricCard
              label="Next unlocks"
              value={insightsLoading ? "..." : insights?.next_up_recipe_count ?? 0}
              caption="Good options that need one short grocery top-up."
            />
            <InsightMetricCard
              label="Strongest zone"
              value={strongestZone?.count ? strongestZone.label : "None yet"}
              caption={strongestZone?.count ? strongestZone.description : "Once you add ingredients, NutriSync will show your strongest pantry zone."}
            />
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <div className="surface-card p-6 sm:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="section-title">Pantry zones</h2>
              <p className="muted-copy mt-1">A quick read on where your kitchen is strong, thin, or underpowered.</p>
            </div>
          </div>
          <div className="mt-6 grid gap-4">
            {insights?.zones?.length ? (
              insights.zones.map((zone) => <ZoneCard key={zone.label} zone={zone} />)
            ) : (
              <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
                Pantry zones appear once you add or scan ingredients.
              </div>
            )}
          </div>
        </div>

        <div className="surface-card p-6 sm:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="section-title">Unlock ingredients</h2>
              <p className="muted-copy mt-1">The smartest single additions if you want more recipe coverage fast.</p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {insights?.unlock_ingredients?.length ? (
              insights.unlock_ingredients.map((suggestion) => (
                <UnlockSuggestion key={suggestion.ingredient} suggestion={suggestion} />
              ))
            ) : (
              <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist">
                Once NutriSync sees enough overlap across recipes, it will suggest the most valuable next ingredient to buy.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="surface-card p-6 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="section-title">Tonight&apos;s lineup</h2>
            <p className="muted-copy mt-1">A few high-signal recipe paths chosen from your current pantry, not just generic top picks.</p>
          </div>
          <button type="button" onClick={handleFindRecipes} disabled={!ingredients.length} className="secondary-button">
            Open Recommendation Board
          </button>
        </div>

        <div className="mt-6 grid gap-4 xl:grid-cols-3">
          {insights?.spotlight_recipes?.length ? (
            insights.spotlight_recipes.map((recipe) => (
              <SpotlightRecipeCard key={recipe.id} recipe={recipe} onView={() => navigate(`/recipes/${recipe.id}`)} />
            ))
          ) : (
            <div className="rounded-[24px] border border-dashed border-sand bg-white/70 p-6 text-sm text-mist xl:col-span-3">
              Scan or add a few ingredients first, then NutriSync will surface the strongest recipe paths from your actual pantry.
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );
}
