from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

from config import MOCK_CV_MODE

MOCK_INGREDIENTS = ["chicken breast", "spinach", "lentils", "olive oil", "garlic"]
SCAN_UNAVAILABLE_MESSAGE = (
    "Image scanning is temporarily unavailable on this device. Please try again later or add ingredients manually."
)
CLIP_MODEL_NAME = "ViT-B/32"
CLIP_TOPK_PER_VIEW = 6
CLIP_MIN_VIEW_SCORE = 0.08
CLIP_MIN_KEEP_MAX = 0.16
CLIP_MIN_KEEP_SUM = 0.28
CLIP_RELATIVE_KEEP_RATIO = 0.18
CLIP_STRONG_KEEP_MAX = 0.72
CLIP_DOMINANT_SINGLE_MIN_HITS = 4
CLIP_DOMINANT_SINGLE_MIN_SUM = 1.2
CLIP_DOMINANT_SINGLE_MIN_MAX = 0.25
CLIP_DOMINANT_SINGLE_SECONDARY_RATIO = 0.65
CLIP_STANDOUT_SINGLE_MIN_MAX = 0.8
CLIP_STANDOUT_SINGLE_SECONDARY_RATIO = 0.55
LOW_VISUAL_SUPPORT_INGREDIENTS = {
    "broth",
    "ghee",
    "olive oil",
    "protein powder",
    "sesame oil",
}
CLIP_LABEL_ALIASES = {
    "bread": ("bread", "bread loaf", "loaf of bread"),
    "chicken breast": ("chicken breast", "raw chicken breast", "grilled chicken breast"),
    "egg": ("egg", "eggs", "whole egg"),
    "greek yogurt": ("greek yogurt", "strained yogurt", "yogurt"),
    "milk": ("milk", "glass of milk"),
    "onion": ("onion", "red onion", "white onion", "whole onion", "onion bulb"),
    "paneer": ("paneer", "paneer cubes", "indian cottage cheese"),
    "rice": ("rice", "cooked rice", "bowl of rice"),
    "tofu": ("tofu", "bean curd", "fried tofu", "tofu cubes"),
}
LABEL_TO_INGREDIENT = {
    "acorn squash": "squash",
    "apple": "apple",
    "artichoke": "artichoke",
    "asparagus": "asparagus",
    "avocado": "avocado",
    "bagel": "bread",
    "banana": "banana",
    "bean": "beans",
    "bell pepper": "bell pepper",
    "black bean": "beans",
    "broccoli": "broccoli",
    "brussels sprout": "broccoli",
    "burrito": "beans",
    "cabbage": "cabbage",
    "capsicum": "bell pepper",
    "carbonara": "pasta",
    "carrot": "carrot",
    "cauliflower": "cauliflower",
    "cheeseburger": "beef",
    "chickpea": "chickpeas",
    "consomme": "broth",
    "corn": "corn",
    "croissant": "bread",
    "cucumber": "cucumber",
    "custard apple": "apple",
    "egg": "egg",
    "eggplant": "eggplant",
    "fig": "fig",
    "french loaf": "bread",
    "garlic": "garlic",
    "ginger": "ginger",
    "granny smith": "apple",
    "green bean": "beans",
    "guacamole": "avocado",
    "head cabbage": "cabbage",
    "hotdog": "sausage",
    "jackfruit": "jackfruit",
    "kidney bean": "rajma",
    "kiwi": "kiwi",
    "leek": "onion",
    "lemon": "lemon",
    "lentil": "lentils",
    "lettuce": "spinach",
    "lime": "lemon",
    "mango": "mango",
    "meat loaf": "ground meat",
    "mushroom": "mushroom",
    "noodle": "pasta",
    "okra": "okra",
    "omelet": "egg",
    "omelette": "egg",
    "onion": "onion",
    "orange": "orange",
    "papaya": "papaya",
    "pasta": "pasta",
    "pea": "peas",
    "pineapple": "pineapple",
    "pomegranate": "pomegranate",
    "potato": "potato",
    "potpie": "mixed vegetables",
    "pretzel": "bread",
    "pumpkin": "pumpkin",
    "radish": "radish",
    "rice": "rice",
    "roll": "bread",
    "sausage": "sausage",
    "scallion": "onion",
    "shallot": "onion",
    "soybean": "soy granules",
    "spaghetti squash": "squash",
    "spinach": "spinach",
    "strawberry": "strawberry",
    "sweet potato": "sweet potato",
    "taco": "beans",
    "tomato": "tomato",
    "walnut": "nuts",
    "yoghurt": "greek yogurt",
    "yogurt": "greek yogurt",
    "zucchini": "zucchini",
}
NON_INGREDIENT_LABELS = {
    "dining table",
    "grocery store",
    "plate",
    "restaurant",
    "supermarket",
}
SCAN_SUBPROCESS_ENV_OVERRIDES = {
    "HF_HUB_DISABLE_XET": "1",
    "KMP_DUPLICATE_LIB_OK": "TRUE",
    "KMP_INIT_AT_FORK": "FALSE",
    "OMP_NUM_THREADS": "1",
}
CLIP_SCAN_SCRIPT = """
import clip
import json
import sys

import torch
from PIL import Image, ImageOps


def build_views(image):
    width, height = image.size
    crop_size = int(min(width, height) * 0.72)
    if crop_size < 96:
        return [image]

    offsets = [
        (0, 0),
        (max(0, width - crop_size), 0),
        (0, max(0, height - crop_size)),
        (max(0, width - crop_size), max(0, height - crop_size)),
        (max(0, (width - crop_size) // 2), max(0, (height - crop_size) // 2)),
    ]

    views = [image]
    seen_bounds = set()
    for left, top in offsets:
        bounds = (left, top, left + crop_size, top + crop_size)
        if bounds in seen_bounds:
            continue
        seen_bounds.add(bounds)
        views.append(image.crop(bounds))
    return views


path = sys.argv[1]
specs = json.loads(sys.argv[2])
image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
model, preprocess = clip.load("ViT-B/32", device="cpu")
prompts = [spec["prompt"] for spec in specs]
text = clip.tokenize(prompts)

with torch.no_grad():
    text_features = model.encode_text(text)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    aggregate = {}
    for view in build_views(image):
        image_tensor = preprocess(view).unsqueeze(0)
        image_features = model.encode_image(image_tensor)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        probabilities = (100.0 * image_features @ text_features.T).softmax(dim=-1)[0]
        values, indices = probabilities.topk(min(18, len(specs)))
        view_scores = {}
        for score, index in zip(values.tolist(), indices.tolist()):
            ingredient = specs[index]["ingredient"]
            view_scores[ingredient] = max(view_scores.get(ingredient, 0.0), float(score))
        for ingredient, score in view_scores.items():
            stats = aggregate.setdefault(ingredient, {"max": 0.0, "sum": 0.0, "hits": 0})
            stats["max"] = max(stats["max"], score)
            if score >= 0.08:
                stats["sum"] += score
                stats["hits"] += 1

results = [
    {"label": label, "max": stats["max"], "sum": stats["sum"], "hits": stats["hits"]}
    for label, stats in aggregate.items()
]
print(json.dumps(results))
"""
TORCH_SCAN_SCRIPT = """
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from PIL import Image, ImageOps
import torch
from torchvision import models, transforms
from torchvision.models import MobileNet_V2_Weights


def build_views(image):
    width, height = image.size
    crop_size = int(min(width, height) * 0.72)
    if crop_size < 96:
        return [image]

    offsets = [
        (0, 0),
        (max(0, width - crop_size), 0),
        (0, max(0, height - crop_size)),
        (max(0, width - crop_size), max(0, height - crop_size)),
        (max(0, (width - crop_size) // 2), max(0, (height - crop_size) // 2)),
    ]

    views = [image]
    seen_bounds = set()
    for left, top in offsets:
        bounds = (left, top, left + crop_size, top + crop_size)
        if bounds in seen_bounds:
            continue
        seen_bounds.add(bounds)
        views.append(image.crop(bounds))
    return views


path = sys.argv[1]
image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")

weights = MobileNet_V2_Weights.DEFAULT
model = models.mobilenet_v2(weights=weights)
model.eval()
preprocess = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)
labels = weights.meta.get("categories", [])
views = build_views(image)
tensor = torch.stack([preprocess(view) for view in views])

with torch.no_grad():
    predictions = model(tensor)
    scores = predictions.softmax(dim=1)
    values, indices = scores.topk(5, dim=1)

label_scores = {}
for row_values, row_indices in zip(values.tolist(), indices.tolist()):
    for score, index in zip(row_values, row_indices):
        if index >= len(labels):
            continue
        label = labels[index]
        if score > label_scores.get(label, 0.0):
            label_scores[label] = score

results = [
    {"label": label, "confidence": score}
    for label, score in sorted(label_scores.items(), key=lambda item: item[1], reverse=True)[:20]
]
print(json.dumps(results))
"""


class ScanBackendUnavailable(RuntimeError):
    pass


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _decode_image(image_base64: str | None, image_bytes: bytes | None) -> Image.Image | None:
    if image_bytes:
        return ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    if image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        return ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(image_base64)))).convert("RGB")
    return None


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def _label_fragments(label: str) -> list[str]:
    normalized = _normalize_text(label)
    if not normalized:
        return []

    fragments = {normalized}
    for fragment in re.split(r"[,/;()]", normalized):
        fragment = fragment.strip()
        if fragment:
            fragments.add(fragment)
    return sorted(fragments, key=len, reverse=True)


def _build_views(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    crop_size = int(min(width, height) * 0.72)
    if crop_size < 96:
        return [image]

    offsets = [
        (0, 0),
        (max(0, width - crop_size), 0),
        (0, max(0, height - crop_size)),
        (max(0, width - crop_size), max(0, height - crop_size)),
        (max(0, (width - crop_size) // 2), max(0, (height - crop_size) // 2)),
    ]

    views = [image]
    seen_bounds = set()
    for left, top in offsets:
        bounds = (left, top, left + crop_size, top + crop_size)
        if bounds in seen_bounds:
            continue
        seen_bounds.add(bounds)
        views.append(image.crop(bounds))
    return views


@lru_cache(maxsize=1)
def _known_ingredients() -> tuple[str, ...]:
    ingredients = {
        "apple",
        "avocado",
        "banana",
        "beans",
        "beef",
        "bell pepper",
        "bread",
        "broccoli",
        "broth",
        "cabbage",
        "carrot",
        "cauliflower",
        "chickpeas",
        "coffee",
        "corn",
        "cucumber",
        "egg",
        "eggplant",
        "fig",
        "garlic",
        "ginger",
        "greek yogurt",
        "ground meat",
        "jackfruit",
        "kiwi",
        "lemon",
        "lentils",
        "mango",
        "mushroom",
        "nuts",
        "okra",
        "onion",
        "orange",
        "papaya",
        "pasta",
        "peas",
        "pineapple",
        "pomegranate",
        "potato",
        "pumpkin",
        "radish",
        "rajma",
        "rice",
        "sausage",
        "soy granules",
        "spinach",
        "squash",
        "strawberry",
        "sweet potato",
        "tomato",
        "zucchini",
    }

    recipes_path = Path(__file__).resolve().parents[1] / "data" / "recipes.json"
    try:
        payload = json.loads(recipes_path.read_text(encoding="utf-8"))
    except Exception:
        payload = []

    for recipe in payload:
        for ingredient in recipe.get("ingredients", []):
            normalized = _normalize_text(str(ingredient.get("name", "")))
            if normalized:
                ingredients.add(normalized)

    return tuple(sorted(ingredients))


def _run_scan_subprocess(script: str, image: Image.Image, *extra_args: str) -> subprocess.CompletedProcess[str] | None:
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            temp_path = Path(handle.name)

        image.save(temp_path, format="JPEG", quality=95)
        env = os.environ.copy()
        env.update(SCAN_SUBPROCESS_ENV_OVERRIDES)
        return subprocess.run(
            [sys.executable, "-c", script, str(temp_path), *extra_args],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@lru_cache(maxsize=1)
def _clip_prompt_specs() -> tuple[tuple[str, str], ...]:
    specs: list[tuple[str, str]] = []
    for ingredient in _known_ingredients():
        aliases = CLIP_LABEL_ALIASES.get(ingredient, (ingredient,))
        seen_aliases = set()
        for alias in aliases:
            normalized_alias = _normalize_text(alias)
            if not normalized_alias or normalized_alias in seen_aliases:
                continue
            seen_aliases.add(normalized_alias)
            specs.append((ingredient, f"a photo of {normalized_alias}"))
    return tuple(specs)


def _classify_with_clip_scores(image: Image.Image) -> dict[str, dict[str, float | int]] | None:
    prompt_specs = [
        {"ingredient": ingredient, "prompt": prompt}
        for ingredient, prompt in _clip_prompt_specs()
    ]
    completed = _run_scan_subprocess(CLIP_SCAN_SCRIPT, image, json.dumps(prompt_specs))
    if completed is None or completed.returncode != 0:
        return None

    stdout = completed.stdout.strip()
    if not stdout:
        return None

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    stats: dict[str, dict[str, float | int]] = {}
    if not isinstance(payload, list):
        return None

    for item in payload:
        if not isinstance(item, dict):
            continue
        label = _normalize_text(str(item.get("label", "")))
        if label not in _known_ingredients():
            continue
        try:
            max_score = float(item.get("max", 0.0))
            total_score = float(item.get("sum", 0.0))
            hits = int(item.get("hits", 0))
        except (TypeError, ValueError):
            continue
        stats[label] = {"max": max_score, "sum": total_score, "hits": hits}

    return stats or None


def _select_clip_ingredients(
    score_map: dict[str, dict[str, float | int]],
    min_keep_max: float = CLIP_MIN_KEEP_MAX,
    min_keep_sum: float = CLIP_MIN_KEEP_SUM,
    relative_keep_ratio: float = CLIP_RELATIVE_KEEP_RATIO,
    strong_keep_max: float = CLIP_STRONG_KEEP_MAX,
) -> list[str]:
    ranked = sorted(
        score_map.items(),
        key=lambda item: (
            -float(item[1].get("sum", 0.0)),
            -float(item[1].get("max", 0.0)),
            -int(item[1].get("hits", 0)),
            item[0],
        ),
    )
    picked = [
        (label, stats)
        for label, stats in ranked
        if float(stats.get("max", 0.0)) >= min_keep_max or float(stats.get("sum", 0.0)) >= min_keep_sum
    ]
    if not picked:
        return []

    top_label, top_stats = picked[0]
    if top_label not in LOW_VISUAL_SUPPORT_INGREDIENTS:
        refined = [picked[0]]
        top_sum = float(top_stats.get("sum", 0.0))
        top_max = float(top_stats.get("max", 0.0))
        for label, stats in picked[1:]:
            if label not in LOW_VISUAL_SUPPORT_INGREDIENTS:
                refined.append((label, stats))
                continue
            if float(stats.get("sum", 0.0)) >= top_sum * 0.9 and float(stats.get("max", 0.0)) >= top_max * 0.9:
                refined.append((label, stats))
        picked = refined

    top_label, top_stats = picked[0]
    top_sum = float(top_stats.get("sum", 0.0))
    top_max = float(top_stats.get("max", 0.0))
    top_hits = int(top_stats.get("hits", 0))
    second_sum = float(picked[1][1].get("sum", 0.0)) if len(picked) > 1 else 0.0
    if (
        top_hits >= CLIP_DOMINANT_SINGLE_MIN_HITS
        and top_sum >= CLIP_DOMINANT_SINGLE_MIN_SUM
        and top_max >= CLIP_DOMINANT_SINGLE_MIN_MAX
        and second_sum <= top_sum * CLIP_DOMINANT_SINGLE_SECONDARY_RATIO
    ):
        return [top_label]
    if top_max >= CLIP_STANDOUT_SINGLE_MIN_MAX and second_sum <= top_max * CLIP_STANDOUT_SINGLE_SECONDARY_RATIO:
        return [top_label]

    top_sum = float(picked[0][1].get("sum", 0.0))
    threshold = max(0.18, top_sum * relative_keep_ratio)
    filtered = [
        label
        for label, stats in picked
        if float(stats.get("sum", 0.0)) >= threshold or float(stats.get("max", 0.0)) >= strong_keep_max
    ]
    return filtered[:6]


def _map_labels_to_ingredients(labels: list[tuple[str, float]]) -> list[str]:
    ingredient_scores: dict[str, float] = {}

    for label, confidence in labels:
        weight = max(float(confidence), 0.01)
        for fragment in _label_fragments(label):
            if any(_contains_phrase(fragment, blocked) for blocked in NON_INGREDIENT_LABELS):
                continue

            matches = set()
            for source, target in LABEL_TO_INGREDIENT.items():
                if _contains_phrase(fragment, source):
                    matches.add(target)

            for ingredient in _known_ingredients():
                if _contains_phrase(fragment, ingredient):
                    matches.add(ingredient)

            for ingredient in matches:
                ingredient_scores[ingredient] = ingredient_scores.get(ingredient, 0.0) + weight

    ranked = sorted(ingredient_scores.items(), key=lambda item: (-item[1], item[0]))
    return [ingredient for ingredient, _ in ranked[:6]]


def _classify_with_torch_labels(image: Image.Image) -> list[tuple[str, float]] | None:
    completed = _run_scan_subprocess(TORCH_SCAN_SCRIPT, image)
    if completed is None or completed.returncode != 0:
        return None

    stdout = completed.stdout.strip()
    if not stdout:
        return None

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    results: list[tuple[str, float]] = []
    if not isinstance(payload, list):
        return None

    for item in payload:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        results.append((label, confidence))

    return results or None


def detect_ingredients(image_base64: str | None = None, image_bytes: bytes | None = None) -> list[str]:
    if MOCK_CV_MODE:
        return MOCK_INGREDIENTS

    image = _decode_image(image_base64, image_bytes)
    if image is None:
        return []

    clip_scores = _classify_with_clip_scores(image)
    if clip_scores:
        clip_ingredients = _select_clip_ingredients(clip_scores)
        if clip_ingredients:
            return clip_ingredients

    labels = _classify_with_torch_labels(image)
    if labels:
        fallback_ingredients = _map_labels_to_ingredients(labels)
        if fallback_ingredients:
            return fallback_ingredients

    raise ScanBackendUnavailable(SCAN_UNAVAILABLE_MESSAGE)
