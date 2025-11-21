
import yaml

class RuleEngine:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)
        self.min_conf = float(self.cfg.get("min_confidence", 0.7))
        self.rules = self.cfg.get("rules", [])

    def apply(self, dets: list[dict], metrics: dict):
        """
        Apply rules to detections and calculate aggregate confidence scores
        
        Calculates:
        - good_confidence: Average of all 'good' detection confidences
        - bad_confidence: Average of all 'bad' detection confidences
        - Overall pass/fail based on which confidence is higher
        """
        # Calculate aggregate confidence by class
        good_confidence_sum = 0.0
        bad_confidence_sum = 0.0
        good_count = 0
        bad_count = 0
        
        for d in dets:
            label = d.get("label", "").lower()
            conf = d.get("conf", 0.0) * 100  # Convert to percentage
            
            if label == "good":
                good_confidence_sum += conf
                good_count += 1
            elif label == "bad":
                bad_confidence_sum += conf
                bad_count += 1
        
        # Calculate averages
        good_confidence = (good_confidence_sum / good_count) if good_count > 0 else 0.0
        bad_confidence = (bad_confidence_sum / bad_count) if bad_count > 0 else 0.0
        
        # If only one class present, report its average confidence; if both, normalize to sum 100%.
        if good_count > 0 and bad_count == 0:
            # Only good detected
            # good_confidence stays as average, bad_confidence is 0
            pass
        elif bad_count > 0 and good_count == 0:
            # Only bad detected
            # bad_confidence stays as average, good_confidence is 0
            pass
        else:
            # Both detected, normalize to sum 100%
            total = good_confidence + bad_confidence
            if total > 0:
                good_confidence = (good_confidence / total) * 100
                bad_confidence = (bad_confidence / total) * 100
            else:
                good_confidence = 0.0
                bad_confidence = 0.0
            
        # Default decision structure
        decision = {
            "pass": False, 
            "grade": None, 
            "confidence": 0.0,
            "good_confidence": good_confidence,
            "bad_confidence": bad_confidence,
            "good_count": good_count,
            "bad_count": bad_count,
            "reason_codes": []
        }
        
        if not dets:
            # No detections found - mark as FAIL
            decision["reason_codes"].append("NO_DETECTIONS")
            decision["confidence"] = 0.0
        else:
            # Determine pass/fail based on aggregate confidence
            if good_confidence > bad_confidence:
                decision["pass"] = True
                decision["confidence"] = good_confidence
                decision["grade"] = "A"
                decision["reason_codes"].append("GOOD_BREAD_DETECTED")
            elif bad_confidence > good_confidence:
                decision["pass"] = False
                decision["confidence"] = bad_confidence
                decision["grade"] = None
                decision["reason_codes"].append("BAD_BREAD_DETECTED")
            else:
                # Equal confidence - default to fail for safety
                decision["pass"] = False
                decision["confidence"] = max(good_confidence, bad_confidence)
                decision["reason_codes"].append("UNCERTAIN_QUALITY")
            
            # Only apply minimum confidence check if total confidence is very low
            # This prevents false positives when model is uncertain
            total_confidence = good_confidence + bad_confidence
            if total_confidence < 10.0:  # Less than 10% total confidence
                decision["pass"] = False
                if "LOW_CONFIDENCE" not in decision["reason_codes"]:
                    decision["reason_codes"].append("LOW_CONFIDENCE")
                
        # NOTE: Custom rules from YAML config are DISABLED for aggregate confidence mode
        # The aggregate good vs bad confidence is the primary decision logic
        # If you need custom rules, they should be applied before this method
                
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
