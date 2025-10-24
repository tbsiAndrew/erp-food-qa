import os
from functools import lru_cache

LABELS_PATH_DEFAULT = os.getenv("LABELS_PATH", "models/labels.txt")

@lru_cache(maxsize=1)
def load_labels(path: str | None = None) -> dict[int, str]:
    path = path or LABELS_PATH_DEFAULT
    labels: dict[int, str] = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                name = line.strip()
                if name:
                    labels[i] = name
    return labels

def get_label(index: int) -> str:
    labels = load_labels()
    return labels.get(index, f"class_{index}")