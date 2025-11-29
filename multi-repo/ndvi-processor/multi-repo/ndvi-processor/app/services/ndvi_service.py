from dataclasses import dataclass

import numpy as np
import rasterio


@dataclass
class NDVIStats:
    mean: float
    min: float
    max: float


def compute_ndvi_from_tif(path: str, red_band: int = 3, nir_band: int = 4) -> NDVIStats:
    """Compute NDVI = (NIR - RED) / (NIR + RED) from a GeoTIFF.

    - `red_band` / `nir_band` are 1-based band indices.
    - This function reads the requested bands into memory, so it is suitable
      for small to medium tiles. For very large scenes consider windowed IO.
    """
    with rasterio.open(path) as ds:
        red = ds.read(red_band).astype("float32")
        nir = ds.read(nir_band).astype("float32")

    denom = nir + red
    denom[denom == 0] = np.nan
    ndvi = (nir - red) / denom

    valid = ~np.isnan(ndvi)
    if not np.any(valid):
        raise ValueError("No valid NDVI pixels in scene")

    vals = ndvi[valid]
    return NDVIStats(
        mean=float(np.nanmean(vals)),
        min=float(np.nanmin(vals)),
        max=float(np.nanmax(vals)),
    )
