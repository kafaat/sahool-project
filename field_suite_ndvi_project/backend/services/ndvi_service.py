import io
import numpy as np
import rasterio
from rasterio.enums import Resampling
from shapely.geometry import Polygon
from skimage import measure
import matplotlib.pyplot as plt
import rasterio.transform


class NDVIService:

    @staticmethod
    def load_band(path: str):
        return rasterio.open(path)

    @staticmethod
    def compute_ndvi(red_path: str, nir_path: str):
        red = NDVIService.load_band(red_path)
        nir = NDVIService.load_band(nir_path)

        if red.shape != nir.shape:
            nir_data = nir.read(
                1,
                out_shape=(red.count, red.height, red.width),
                resampling=Resampling.bilinear,
            )[0]
        else:
            nir_data = nir.read(1)

        red_data = red.read(1).astype(np.float32)
        nir_data = nir_data.astype(np.float32)

        ndvi = (nir_data - red_data) / (nir_data + red_data + 1e-9)

        return ndvi, red.transform

    @staticmethod
    def ndvi_to_polygon(ndvi: np.ndarray, transform, threshold: float = 0.4):
        mask = ndvi > threshold
        contours = measure.find_contours(mask, 0.5)

        polygons = []
        for contour in contours:
            lon_lat = []
            for row, col in contour:
                x, y = rasterio.transform.xy(transform, row, col)
                lon_lat.append((x, y))
            if len(lon_lat) > 3:
                polygons.append(Polygon(lon_lat))

        if not polygons:
            return None

        largest = max(polygons, key=lambda p: p.area)
        return largest

    @staticmethod
    def ndvi_zones(ndvi: np.ndarray, transform, n_zones: int = 3):
        flat = ndvi[~np.isnan(ndvi)].flatten()
        if flat.size < 10:
            return []

        quantiles = np.quantile(flat, np.linspace(0, 1, n_zones + 1))

        zones_polygons = []

        for i in range(n_zones):
            low = quantiles[i]
            high = quantiles[i + 1]
            mask = (ndvi >= low) & (ndvi <= high)

            contours = measure.find_contours(mask, 0.5)
            polys = []
            for contour in contours:
                lon_lat = []
                for row, col in contour:
                    x, y = rasterio.transform.xy(transform, row, col)
                    lon_lat.append((x, y))
                if len(lon_lat) > 3:
                    polys.append(Polygon(lon_lat))

            if not polys:
                continue

            merged = max(polys, key=lambda p: p.area)
            zones_polygons.append({
                "level": i + 1,
                "range": (float(low), float(high)),
                "polygon": merged
            })

        return zones_polygons

    @staticmethod
    def ndvi_heatmap_png(ndvi: np.ndarray) -> bytes:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.axis("off")
        im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
