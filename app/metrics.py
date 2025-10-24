import cv2
import numpy as np


# approximate mm per pixel if calibrated; set in settings or infer per line
_MM_PER_PX = 0.1


def compute_metrics(bgr):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    mean_lab = lab.reshape(-1, 3).mean(axis=0).tolist()


    # area via simple threshold on L channel (demo placeholder)
    L = lab[:, :, 0]
    _, th = cv2.threshold(L, 0, 255, cv2.THRESH_OTSU)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area_px = max((cv2.contourArea(c) for c in cnts), default=0)
    area_mm2 = float(area_px * (_MM_PER_PX ** 2))


    return {
    "mean_lab": mean_lab, # [L, a, b]
    "area_mm2": area_mm2,
    }