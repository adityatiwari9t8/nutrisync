import { NavLink } from "react-router-dom";

const links = [
  { label: "Dashboard", to: "/" },
  { label: "Pantry", to: "/pantry" },
  { label: "Recipes", to: "/recipes" },
  { label: "Tracker", to: "/tracker" },
  { label: "Dietitian", to: "/dietitian" },
];

export default function Navbar({ user, onLogout }) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/70 bg-white/75 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand text-lg font-extrabold text-white">
            N
          </div>
          <div>
            <p className="text-lg font-bold tracking-tight text-ink">NutriSync</p>
            <p className="text-xs uppercase tracking-[0.2em] text-mist">Macro-guided meal planning</p>
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-medium transition ${
                  isActive ? "bg-brand text-white" : "bg-surface text-ink hover:bg-brand/10"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-ink">{user?.username}</p>
            <p className="text-xs text-mist">{user?.is_premium ? "Premium member" : "Free tier"}</p>
          </div>
          {user?.is_premium && (
            <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
              Premium
            </span>
          )}
          <button type="button" onClick={onLogout} className="secondary-button">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
