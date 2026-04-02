import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import api, { getErrorMessage } from "../api/api";
import IngredientTag from "../components/IngredientTag";

const defaultGoals = { protein: 140, carbs: 180, fat: 55, calories: 2100 };

export default function PantryScan() {
  const navigate = useNavigate();
  const [ingredients, setIngredients] = useState([]);
  const [goals, setGoals] = useState(defaultGoals);
  const [manualIngredient, setManualIngredient] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const uploadInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const cameraInputRef = useRef(null);

  useEffect(() => {
    const loadPantry = async () => {
      try {
        const [pantryResponse, dailyResponse] = await Promise.all([
          api.get("/pantry/ingredients"),
          api.get("/tracker/daily"),
        ]);
        setIngredients(pantryResponse.data.ingredients || []);
        if (dailyResponse.data?.goals) {
          const nextGoals = dailyResponse.data.goals;
          if (Object.values(nextGoals).some((value) => value > 0)) {
            setGoals(nextGoals);
          }
        }
      } catch {
        // The empty state is fine here.
      }
    };

    loadPantry();

    return () => {
      stopCamera();
    };
  }, []);

  const uploadImage = async (file) => {
    if (!file?.type?.startsWith("image/")) {
      setError("Please choose an image file to scan.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");
    setCameraError("");
    try {
      const { data } = await api.post("/pantry/scan", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setIngredients(data.ingredients || []);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to scan that image right now."));
    } finally {
      setLoading(false);
    }
  };

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

  const handleManualAdd = () => {
    const normalized = manualIngredient.trim().toLowerCase();
    if (!normalized || ingredients.includes(normalized)) {
      setManualIngredient("");
      return;
    }
    setIngredients((current) => [...current, normalized]);
    setManualIngredient("");
  };

  const handleGoalChange = (event) => {
    const { name, value } = event.target;
    setGoals((current) => ({ ...current, [name]: Number(value) }));
  };

  const handleFindRecipes = () => {
    navigate("/recipes", { state: { ingredients, macroGoals: goals } });
  };

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page-shell space-y-6">
      <div className="surface-card p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Ingredient detection</p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Scan your fridge or pantry</h1>
            <p className="mt-4 text-base text-mist">
              Use a live camera scan or upload a clear photo, confirm the ingredient list, and
              send it into a recommendation flow tuned to your daily nutrition targets.
            </p>
          </div>

          <div className="rounded-[28px] bg-white/75 p-5">
            <p className="text-sm font-semibold text-ink">What happens next</p>
            <div className="mt-4 space-y-3 text-sm text-mist">
              <p>1. NutriSync detects likely ingredients from your live scan or photo.</p>
              <p>2. You can remove false positives and add staples or condiments manually.</p>
              <p>3. Your final pantry list powers recipe ranking around macro fit and pantry usage.</p>
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
                    onRemove={() => setIngredients((current) => current.filter((item) => item !== ingredient))}
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
              <button type="button" onClick={handleManualAdd} className="secondary-button sm:min-w-40">
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
            <p className="text-sm font-semibold text-ink">Recommendation strategy</p>
            <p className="mt-2 text-sm text-mist">
              The top results combine pantry overlap, macro compliance, and learned preference
              signals to surface meals that are practical to cook tonight.
            </p>
          </div>

          <button
            type="button"
            disabled={!ingredients.length}
            onClick={handleFindRecipes}
            className="primary-button mt-8 w-full"
          >
            Generate Recommendations
          </button>
        </div>
      </div>
    </motion.section>
  );
}
