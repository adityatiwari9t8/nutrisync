import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage } from "../api/api";
import RecipeCard from "../components/RecipeCard";

export default function Recipes() {
  const location = useLocation();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [macroGoals, setMacroGoals] = useState({ protein: 0, carbs: 0, fat: 0, calories: 0 });
  const [sortBy, setSortBy] = useState("best");
  const [loading, setLoading] = useState(true);
  const [loggingId, setLoggingId] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadRecommendations = async () => {
      setLoading(true);
      setError("");
      setStatus("");
      try {
        let nextIngredients = location.state?.ingredients || [];
        let nextGoals = location.state?.macroGoals || null;

        if (!nextIngredients.length) {
          const [pantryResponse, dailyResponse] = await Promise.all([
            api.get("/pantry/ingredients"),
            api.get("/tracker/daily"),
          ]);
          nextIngredients = pantryResponse.data.ingredients || [];
          nextGoals = dailyResponse.data.goals;
        }

        setIngredients(nextIngredients);
        setMacroGoals(nextGoals || { protein: 0, carbs: 0, fat: 0, calories: 0 });

        if (!nextIngredients.length) {
          setRecommendations([]);
          return;
        }

        const { data } = await api.post("/recipes/recommend", {
          ingredients: nextIngredients,
          macro_goals: nextGoals || { protein: 0, carbs: 0, fat: 0, calories: 0 },
        });
        setRecommendations(data);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Unable to load recipe recommendations."));
      } finally {
        setLoading(false);
      }
    };

    loadRecommendations();
  }, [location.state]);

  const sortedRecommendations = [...recommendations].sort((left, right) => {
    if (sortBy === "protein") {
      return right.protein_g - left.protein_g;
    }
    if (sortBy === "waste") {
      return right.waste_score - left.waste_score;
    }
    return right.hybrid_score - left.hybrid_score;
  });

  const handleLogMeal = async (recipeId) => {
    setLoggingId(recipeId);
    setStatus("");
    try {
      await api.post("/tracker/log", { recipe_id: recipeId, servings: 1 });
      setStatus("Meal logged successfully.");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to log this meal."));
    } finally {
      setLoggingId(null);
    }
  };

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Top 5 recommendations</p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Macro-optimised meals from your pantry</h1>
            <p className="mt-4 max-w-3xl text-base text-mist">
              Each recommendation balances pantry coverage, nutrition fit, and prior preference
              signals so the shortlist feels both useful and realistic.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: "best", label: "Best Match" },
              { key: "protein", label: "Highest Protein" },
              { key: "waste", label: "Most Pantry Efficient" },
            ].map((option) => (
              <button
                key={option.key}
                type="button"
                onClick={() => setSortBy(option.key)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  sortBy === option.key ? "bg-brand text-white" : "bg-white text-ink hover:bg-brand/10"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {ingredients.map((ingredient) => (
            <span key={ingredient} className="ghost-chip">
              {ingredient}
            </span>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="ghost-chip">Protein target {macroGoals.protein}g</span>
          <span className="ghost-chip">Carbs target {macroGoals.carbs}g</span>
          <span className="ghost-chip">Fat target {macroGoals.fat}g</span>
          <span className="ghost-chip">Calories target {macroGoals.calories}</span>
        </div>

        {error ? <p className="mt-6 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p> : null}
        {status ? <p className="mt-6 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{status}</p> : null}
      </div>

      {loading ? (
        <div className="surface-card p-10 text-center text-sm text-mist">Ranking recipes...</div>
      ) : sortedRecommendations.length ? (
        <div className="grid gap-6 xl:grid-cols-2">
          {sortedRecommendations.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onView={() => navigate(`/recipes/${recipe.id}`)}
              onLog={() => handleLogMeal(recipe.id)}
              loading={loggingId === recipe.id}
            />
          ))}
        </div>
      ) : (
        <div className="surface-card p-10 text-center">
          <h2 className="text-2xl font-semibold text-ink">No recommendations yet</h2>
          <p className="mt-3 text-sm text-mist">
            Add a pantry photo or a few ingredients first so NutriSync can assemble a meaningful shortlist.
          </p>
          <button type="button" onClick={() => navigate("/pantry")} className="primary-button mt-6">
            Scan Pantry
          </button>
        </div>
      )}
    </motion.section>
  );
}
