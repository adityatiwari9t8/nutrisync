import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage } from "../api/api";

export default function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState(null);
  const [servings, setServings] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadRecipe = async () => {
      setLoading(true);
      setError("");
      try {
        const { data } = await api.get(`/recipes/${id}`);
        setRecipe(data);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Unable to load recipe details."));
      } finally {
        setLoading(false);
      }
    };

    loadRecipe();
  }, [id]);

  const handleLog = async () => {
    setStatus("");
    try {
      await api.post("/tracker/log", { recipe_id: Number(id), servings });
      setStatus("Meal logged to your tracker.");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to log this meal."));
    }
  };

  if (loading) {
    return <section className="page-shell"><div className="surface-card p-10 text-center text-sm text-mist">Loading recipe...</div></section>;
  }

  if (!recipe) {
    return <section className="page-shell"><div className="surface-card p-10 text-center text-sm text-mist">{error || "Recipe not found."}</div></section>;
  }

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card overflow-hidden">
        <div className="bg-gradient-to-br from-brand via-brand to-emerald-300 px-6 py-12 text-white sm:px-8">
          <button type="button" onClick={() => navigate(-1)} className="rounded-full bg-white/15 px-4 py-2 text-sm font-semibold backdrop-blur">
            Back
          </button>
          <p className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-white/80">{recipe.cuisine}</p>
          <h1 className="mt-3 text-4xl font-extrabold tracking-tight">{recipe.name}</h1>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="surface-card p-6">
          <h2 className="section-title">Ingredients</h2>
          <div className="mt-5 space-y-3">
            {recipe.ingredients.map((ingredient) => (
              <div key={`${ingredient.name}-${ingredient.quantity}`} className="flex items-center justify-between rounded-[20px] bg-white/80 px-4 py-3">
                <span className="font-medium text-ink">{ingredient.name}</span>
                <span className="text-sm text-mist">
                  {ingredient.quantity} {ingredient.unit}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="surface-card p-6">
          <h2 className="section-title">Instructions</h2>
          <div className="mt-5 space-y-4">
            {recipe.steps.map((step, index) => (
              <div key={step} className="flex gap-4 rounded-[22px] bg-white/80 p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white">
                  {index + 1}
                </div>
                <p className="text-sm leading-6 text-ink">{step}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Protein</p>
              <p className="mt-2 text-2xl font-bold text-ink">{recipe.protein_g}g</p>
            </div>
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Carbs</p>
              <p className="mt-2 text-2xl font-bold text-ink">{recipe.carbs_g}g</p>
            </div>
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Fat</p>
              <p className="mt-2 text-2xl font-bold text-ink">{recipe.fat_g}g</p>
            </div>
            <div className="rounded-[22px] bg-white/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-mist">Calories</p>
              <p className="mt-2 text-2xl font-bold text-ink">{recipe.calories}</p>
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={servings}
              onChange={(event) => setServings(Number(event.target.value))}
              className="input-shell sm:max-w-40"
            />
            <button type="button" onClick={handleLog} className="primary-button">
              Log Meal
            </button>
          </div>

          {error ? <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
          {status ? <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{status}</p> : null}
        </div>
      </div>
    </motion.section>
  );
}
