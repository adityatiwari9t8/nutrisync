import { Suspense, lazy, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import Navbar from "./components/Navbar";
import { clearAuth, getStoredToken, getStoredUser, setUnauthorizedHandler } from "./api/api";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const DietitianPortal = lazy(() => import("./pages/DietitianPortal"));
const Login = lazy(() => import("./pages/Login"));
const PantryScan = lazy(() => import("./pages/PantryScan"));
const RecipeDetail = lazy(() => import("./pages/RecipeDetail"));
const Recipes = lazy(() => import("./pages/Recipes"));
const Register = lazy(() => import("./pages/Register"));
const Tracker = lazy(() => import("./pages/Tracker"));

function ProtectedRoute({ user, children }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [auth, setAuth] = useState({
    token: getStoredToken(),
    user: getStoredUser(),
  });

  const refreshAuth = () => {
    setAuth({
      token: getStoredToken(),
      user: getStoredUser(),
    });
  };

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setAuth({ token: null, user: null });
      navigate("/login", { replace: true });
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, [navigate]);

  const handleLogout = () => {
    clearAuth();
    refreshAuth();
    navigate("/login", { replace: true });
  };

  const isAuthPage = ["/login", "/register"].includes(location.pathname);

  return (
    <div className="min-h-screen">
      {auth.user && !isAuthPage ? <Navbar user={auth.user} onLogout={handleLogout} /> : null}
      <Suspense
        fallback={
          <section className="page-shell">
            <div className="surface-card p-10 text-center text-sm text-mist">Loading NutriSync...</div>
          </section>
        }
      >
        <Routes>
          <Route path="/login" element={<Login onAuthSuccess={refreshAuth} />} />
          <Route path="/register" element={<Register onAuthSuccess={refreshAuth} />} />
          <Route
            path="/"
            element={
              <ProtectedRoute user={auth.user}>
                <Dashboard user={auth.user} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pantry"
            element={
              <ProtectedRoute user={auth.user}>
                <PantryScan />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recipes"
            element={
              <ProtectedRoute user={auth.user}>
                <Recipes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recipes/:id"
            element={
              <ProtectedRoute user={auth.user}>
                <RecipeDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tracker"
            element={
              <ProtectedRoute user={auth.user}>
                <Tracker />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dietitian"
            element={
              <ProtectedRoute user={auth.user}>
                <DietitianPortal />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to={auth.user ? "/" : "/login"} replace />} />
        </Routes>
      </Suspense>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
