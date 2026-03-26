export default function IngredientTag({ label, onRemove }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-brand/10 px-3 py-2 text-sm font-medium text-brand">
      {label}
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          className="flex h-5 w-5 items-center justify-center rounded-full bg-brand/15 text-xs hover:bg-brand/25"
        >
          x
        </button>
      ) : null}
    </span>
  );
}
