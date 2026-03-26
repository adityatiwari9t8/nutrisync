from __future__ import annotations

import base64
import io
from functools import lru_cache

from PIL import Image, ImageOps

from config import MOCK_CV_MODE

MOCK_INGREDIENTS = ["chicken breast", "spinach", "lentils", "olive oil", "garlic"]
INGREDIENT_ALIASES = {
    "acorn squash": "squash",
    "artichoke": "artichoke",
    "bagel": "bread",
    "banana": "banana",
    "bell pepper": "bell pepper",
    "broccoli": "broccoli",
    "burrito": "beans",
    "carbonara": "pasta",
    "cauliflower": "cauliflower",
    "cheeseburger": "beef",
    "consomme": "broth",
    "cucumber": "cucumber",
    "custard apple": "apple",
    "espresso": "coffee",
    "fig": "fig",
    "french loaf": "bread",
    "granny smith": "apple",
    "guacamole": "avocado",
    "head cabbage": "cabbage",
    "hotdog": "sausage",
    "jackfruit": "jackfruit",
    "lemon": "lemon",
    "meat loaf": "ground meat",
    "mushroom": "mushroom",
    "orange": "orange",
    "pineapple": "pineapple",
    "pomegranate": "pomegranate",
    "potpie": "mixed vegetables",
    "pretzel": "bread",
    "spaghetti squash": "squash",
    "strawberry": "strawberry",
    "zucchini": "zucchini",
}
NON_INGREDIENT_LABELS = {
    "dining table",
    "grocery store",
    "plate",
    "restaurant",
    "supermarket",
}


@lru_cache(maxsize=1)
def _load_model_bundle():
    try:
        import torch
        from torchvision import models, transforms
        from torchvision.models import MobileNet_V2_Weights

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
        return torch, model, preprocess, labels
    except Exception:
        return None


def _decode_image(image_base64: str | None, image_bytes: bytes | None) -> Image.Image | None:
    if image_bytes:
        return ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    if image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        return ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(image_base64)))).convert("RGB")
    return None


def _map_labels_to_ingredients(labels: list[str]) -> list[str]:
    detected = []
    for label in labels:
        lowered = label.lower()
        if lowered in NON_INGREDIENT_LABELS:
            continue
        for source, target in INGREDIENT_ALIASES.items():
            if source in lowered and target not in detected:
                detected.append(target)
    return detected[:5]


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


def detect_ingredients(image_base64: str | None = None, image_bytes: bytes | None = None) -> list[str]:
    if MOCK_CV_MODE:
        return MOCK_INGREDIENTS

    bundle = _load_model_bundle()
    if bundle is None:
        return MOCK_INGREDIENTS

    image = _decode_image(image_base64, image_bytes)
    if image is None:
        return []

    torch, model, preprocess, labels = bundle
    views = _build_views(image)
    tensor = torch.stack([preprocess(view) for view in views])

    with torch.no_grad():
        predictions = model(tensor)
        scores = predictions.softmax(dim=1)
        top_indices = scores.topk(3, dim=1).indices.tolist()

    top_labels = []
    for indices in top_indices:
        for index in indices:
            if index < len(labels):
                label = labels[index]
                if label not in top_labels:
                    top_labels.append(label)

    return _map_labels_to_ingredients(top_labels)
