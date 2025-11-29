import numpy as np
from PIL import Image
import requests
from io import BytesIO


def analyze_ndvi_image(ndvi_url: str) -> dict:
    """Load NDVI preview image and compute simple stress statistics.
    This assumes the image is already colorized where G > R for greener areas.
    """
    resp = requests.get(ndvi_url, timeout=60)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    arr = np.array(img)

    # Flatten pixels
    pixels = arr.reshape(-1, 3).astype("float32")
    if pixels.size == 0:
        return {
            "excellent": 0.0,
            "good": 0.0,
            "monitor": 0.0,
            "stress": 0.0,
            "severe": 0.0,
        }

    # Simple proxy: higher (G-R) => healthier vegetation
    green = pixels[:, 1] / 255.0
    red = pixels[:, 0] / 255.0
    ndvi_est = green - red

    # Clip range approximately to [-1,1]
    ndvi_est = np.clip(ndvi_est, -1.0, 1.0)

    excellent = float(np.mean(ndvi_est > 0.6))
    good = float(np.mean((ndvi_est > 0.45) & (ndvi_est <= 0.6)))
    monitor = float(np.mean((ndvi_est > 0.25) & (ndvi_est <= 0.45)))
    stress = float(np.mean((ndvi_est > 0.10) & (ndvi_est <= 0.25)))
    severe = float(np.mean(ndvi_est <= 0.10))

    return {
        "excellent": excellent,
        "good": good,
        "monitor": monitor,
        "stress": stress,
        "severe": severe,
    }
