
import yaml

class RuleEngine:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)
        self.min_conf = float(self.cfg.get("min_confidence", 0.7))
        self.rules = self.cfg.get("rules", [])

    def apply(self, dets: list[dict], metrics: dict):
        # Default to FAIL if no detections (changed from PASS)
        decision = {"pass": False if not dets else True, "grade": None, "confidence": 0.0, "reason_codes": []}
        
        if dets:
            decision["confidence"] = max(d.get("conf", 0.0) for d in dets)
        else:
            # No detections found - mark as FAIL
            decision["reason_codes"].append("NO_DETECTIONS")
            
        for r in self.rules:
            if self._match(r.get("when", {}), dets, metrics):
                act = r.get("action", {})
                decision["pass"] = bool(act.get("pass", decision["pass"]))
                if "grade" in act: decision["grade"] = act["grade"]
                if rc := act.get("reason_codes"): decision["reason_codes"].extend(rc)
                
        if decision["confidence"] < self.min_conf and dets:
            decision["pass"] = False
            decision["reason_codes"].append("LOW_CONFIDENCE")
            
        return decision

    def _match(self, cond: dict, dets: list[dict], metrics: dict) -> bool:
        if "any_detection" in cond:
            spec = cond["any_detection"]
            classes = spec.get("class_in", [])
            conf_gte = float(spec.get("conf_gte", 0.0))
            for d in dets:
                if (not classes or d.get("cls") in classes) and d.get("conf", 0.0) >= conf_gte:
                    return True
            return False
        if "metrics" in cond:
            m = cond["metrics"]
            if "area_mm2" in m:
                area = float(metrics.get("area_mm2", 0.0))
                if "lt" in m["area_mm2"] and not (area < float(m["area_mm2"]["lt"])): return False
                if "gt" in m["area_mm2"] and not (area > float(m["area_mm2"]["gt"])): return False
            if "mean_lab" in m and "L" in m["mean_lab"]:
                L = float(metrics.get("mean_lab", [0])[0])
                if "lt" in m["mean_lab"]["L"] and not (L < float(m["mean_lab"]["L"]["lt"])): return False
                if "gt" in m["mean_lab"]["L"] and not (L > float(m["mean_lab"]["L"]["gt"])): return False
            return True
        return False
