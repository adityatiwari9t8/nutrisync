from __future__ import annotations

import base64
import io
from functools import lru_cache

from PIL import Image

from config import MOCK_CV_MODE

MOCK_INGREDIENTS = ["chicken breast", "spinach", "lentils", "olive oil", "garlic"]


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
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        return Image.open(io.BytesIO(base64.b64decode(image_base64))).convert("RGB")
    return None


def _map_labels_to_ingredients(labels: list[str]) -> list[str]:
    ingredient_map = {
        "broccoli": "broccoli",
        "bell pepper": "bell pepper",
        "zucchini": "zucchini",
        "cucumber": "cucumber",
        "cauliflower": "cauliflower",
        "mushroom": "mushroom",
        "artichoke": "artichoke",
        "spaghetti squash": "squash",
        "pomegranate": "pomegranate",
        "banana": "banana",
        "pineapple": "pineapple",
        "jackfruit": "jackfruit",
        "lemon": "lemon",
        "orange": "orange",
        "granny smith": "apple",
        "strawberry": "strawberry",
        "carbonara": "pasta",
        "guacamole": "avocado",
        "plate": "mixed vegetables",
    }
    detected = []
    for label in labels:
        lowered = label.lower()
        for source, target in ingredient_map.items():
            if source in lowered and target not in detected:
                detected.append(target)
    return detected[:5] or MOCK_INGREDIENTS


def detect_ingredients(image_base64: str | None = None, image_bytes: bytes | None = None) -> list[str]:
    if MOCK_CV_MODE:
        return MOCK_INGREDIENTS

    bundle = _load_model_bundle()
    if bundle is None:
        return MOCK_INGREDIENTS

    image = _decode_image(image_base64, image_bytes)
    if image is None:
        return MOCK_INGREDIENTS

    torch, model, preprocess, labels = bundle
    tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        predictions = model(tensor)
        scores = predictions.softmax(dim=1)
        top_indices = scores.topk(5).indices.squeeze(0).tolist()

    top_labels = [labels[index] for index in top_indices if index < len(labels)]
    return _map_labels_to_ingredients(top_labels)
