import numpy as np
import cv2, onnxruntime as ort, os
from ..labels import get_label

class ONNXDetector:
    def __init__(self, model_path: str, providers: list[str]):
        wanted = providers or []
        available = ort.get_available_providers()
        chosen = [p for p in wanted if p in available] or available or ["CPUExecutionProvider"]
        self.sess = ort.InferenceSession(model_path, providers=chosen)
        self.model_name = os.path.splitext(os.path.basename(model_path))[0]
        self.model_version = "1.1.0"

    def predict(self, bgr):
        inp = self.sess.get_inputs()[0]
        name = inp.name
        shape = inp.shape
        def to_dim(x):
            try:
                return int(x)
            except Exception:
                return 224
        _, c, h, w = [to_dim(s) for s in shape]

        img = cv2.resize(bgr, (w, h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose(2, 0, 1)[None].astype("float32") / 255.0

        out = self.sess.run(None, {name: img})
        logits = out[0]
        if logits.ndim == 2:
            logits = logits[0]
        e = np.exp(logits - np.max(logits))
        probs = e / (np.sum(e) + 1e-9)
        cls = int(np.argmax(probs))
        conf = float(np.max(probs))
        label = get_label(cls)
        return [{
            "cls": str(cls),
            "label": label,
            "conf": conf,
            "box": [0, 0, w, h],
        }]