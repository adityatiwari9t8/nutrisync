export default function RecipeCard({ recipe, onView, onLog, loading = false }) {
  return (
    <article className="surface-card overflow-hidden">
      <div
        role="button"
        tabIndex={0}
        onClick={onView}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            onView();
          }
        }}
        className="cursor-pointer"
      >
        <div className="relative h-44 bg-gradient-to-br from-brand/90 via-brand to-emerald-300 p-5 text-white">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute -right-8 -top-6 h-28 w-28 rounded-full bg-white/20" />
            <div className="absolute bottom-4 left-4 h-14 w-14 rounded-full bg-white/10" />
          </div>
          <div className="relative flex h-full flex-col justify-between">
            <div className="flex items-start justify-between gap-4">
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur">
                {recipe.cuisine}
              </span>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                Pantry usage {Math.round(recipe.waste_score * 100)}%
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-semibold tracking-tight">{recipe.name}</h3>
              <p className="mt-1 text-sm text-white/80">
                Best-match score {Math.round(recipe.hybrid_score * 100)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-5 p-5">
        <div className="flex flex-wrap gap-2">
          <span className="ghost-chip">Protein {recipe.protein_g}g</span>
          <span className="ghost-chip">Carbs {recipe.carbs_g}g</span>
          <span className="ghost-chip">Fat {recipe.fat_g}g</span>
          <span className="ghost-chip">{recipe.calories} kcal</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {recipe.matched_ingredients?.length ? (
            recipe.matched_ingredients.map((ingredient) => (
              <span key={ingredient} className="rounded-full bg-brand/10 px-3 py-1 text-xs font-medium text-brand">
                {ingredient}
              </span>
            ))
          ) : (
            <span className="text-sm text-mist">Ranked from your goals, preferences, and pantry profile.</span>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={onView} className="secondary-button">
            View Details
          </button>
          <button type="button" onClick={onLog} disabled={loading} className="primary-button">
            {loading ? "Logging..." : "Log This Meal"}
          </button>
        </div>
      </div>
    </article>
  );
}
