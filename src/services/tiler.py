"""
Map Tiler Service - Sahool Agricultural Platform
Generates map tiles from satellite imagery and vector data
Supports XYZ, TMS, and WMTS tile formats
"""

import os
import io
import math
from typing import Tuple, Optional, List
from PIL import Image
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TileCoordinate:
    """Represents a tile coordinate in XYZ format"""
    
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"Tile(x={self.x}, y={self.y}, z={self.z})"
    
    def to_bbox(self) -> Tuple[float, float, float, float]:
        """Convert tile coordinates to bounding box (minx, miny, maxx, maxy)"""
        n = 2.0 ** self.z
        minx = self.x / n * 360.0 - 180.0
        maxx = (self.x + 1) / n * 360.0 - 180.0
        
        miny_rad = math.atan(math.sinh(math.pi * (1 - 2 * (self.y + 1) / n)))
        miny = math.degrees(miny_rad)
        
        maxy_rad = math.atan(math.sinh(math.pi * (1 - 2 * self.y / n)))
        maxy = math.degrees(maxy_rad)
        
        return (minx, miny, maxx, maxy)


class GeoUtils:
    """Geospatial utility functions"""
    
    @staticmethod
    def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert latitude/longitude to tile coordinates"""
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        
        lat_rad = math.radians(lat)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        
        return (x, y)
    
    @staticmethod
    def tile_to_lat_lon(x: int, y: int, zoom: int) -> Tuple[float, float]:
        """Convert tile coordinates to latitude/longitude"""
        n = 2.0 ** zoom
        lon = x / n * 360.0 - 180.0
        
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        
        return (lat, lon)
    
    @staticmethod
    def bbox_to_tiles(bbox: Tuple[float, float, float, float], zoom: int) -> List[TileCoordinate]:
        """Get all tiles that intersect with a bounding box"""
        minx, miny, maxx, maxy = bbox
        
        # Get tile coordinates for corners
        x1, y1 = GeoUtils.lat_lon_to_tile(maxy, minx, zoom)
        x2, y2 = GeoUtils.lat_lon_to_tile(miny, maxx, zoom)
        
        # Generate all tiles in range
        tiles = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                tiles.append(TileCoordinate(x, y, zoom))
        
        return tiles


class MapTiler:
    """Main map tiler service"""
    
    def __init__(self, tile_size: int = 256, cache_dir: Optional[str] = None):
        self.tile_size = tile_size
        self.cache_dir = Path(cache_dir) if cache_dir else Path("/tmp/tiles")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_tile_path(self, x: int, y: int, z: int, layer: str = "base") -> Path:
        """Get file path for a tile"""
        return self.cache_dir / layer / str(z) / str(x) / f"{y}.png"
    
    def tile_exists(self, x: int, y: int, z: int, layer: str = "base") -> bool:
        """Check if tile exists in cache"""
        return self.get_tile_path(x, y, z, layer).exists()
    
    def save_tile(self, tile_image: Image.Image, x: int, y: int, z: int, layer: str = "base"):
        """Save tile to cache"""
        tile_path = self.get_tile_path(x, y, z, layer)
        tile_path.parent.mkdir(parents=True, exist_ok=True)
        tile_image.save(tile_path, "PNG", optimize=True)
        logger.debug(f"Saved tile: {tile_path}")
    
    def load_tile(self, x: int, y: int, z: int, layer: str = "base") -> Optional[Image.Image]:
        """Load tile from cache"""
        tile_path = self.get_tile_path(x, y, z, layer)
        if tile_path.exists():
            return Image.open(tile_path)
        return None
    
    def generate_empty_tile(self, transparent: bool = True) -> Image.Image:
        """Generate an empty tile"""
        if transparent:
            return Image.new('RGBA', (self.tile_size, self.tile_size), (0, 0, 0, 0))
        else:
            return Image.new('RGB', (self.tile_size, self.tile_size), (255, 255, 255))
    
    def generate_ndvi_tile(
        self,
        x: int,
        y: int,
        z: int,
        ndvi_data: np.ndarray,
        bbox: Tuple[float, float, float, float]
    ) -> Image.Image:
        """Generate NDVI visualization tile"""
        tile = TileCoordinate(x, y, z)
        tile_bbox = tile.to_bbox()
        
        if not self._bbox_intersects(tile_bbox, bbox):
            return self.generate_empty_tile()
        
        def ndvi_to_color(ndvi_value):
            if ndvi_value < -0.2:
                return (0, 0, 255, 255)
            elif ndvi_value < 0:
                return (165, 42, 42, 255)
            elif ndvi_value < 0.2:
                return (255, 255, 0, 255)
            elif ndvi_value < 0.4:
                return (173, 255, 47, 255)
            elif ndvi_value < 0.6:
                return (0, 255, 0, 255)
            else:
                return (0, 128, 0, 255)
        
        tile_image = Image.new('RGBA', (self.tile_size, self.tile_size), (0, 0, 0, 0))
        pixels = tile_image.load()
        
        for py in range(self.tile_size):
            for px in range(self.tile_size):
                lat = tile_bbox[3] - (py / self.tile_size) * (tile_bbox[3] - tile_bbox[1])
                lon = tile_bbox[0] + (px / self.tile_size) * (tile_bbox[2] - tile_bbox[0])
                
                ndvi_value = self._sample_ndvi(ndvi_data, bbox, lat, lon)
                
                if ndvi_value is not None:
                    pixels[px, py] = ndvi_to_color(ndvi_value)
        
        return tile_image
    
    def _bbox_intersects(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> bool:
        """Check if two bounding boxes intersect"""
        return not (bbox1[2] < bbox2[0] or bbox1[0] > bbox2[2] or
                   bbox1[3] < bbox2[1] or bbox1[1] > bbox2[3])
    
    def _sample_ndvi(
        self,
        ndvi_data: np.ndarray,
        bbox: Tuple[float, float, float, float],
        lat: float,
        lon: float
    ) -> Optional[float]:
        """Sample NDVI value at given lat/lon"""
        minx, miny, maxx, maxy = bbox
        
        if lon < minx or lon > maxx or lat < miny or lat > maxy:
            return None
        
        height, width = ndvi_data.shape
        x_idx = int((lon - minx) / (maxx - minx) * width)
        y_idx = int((maxy - lat) / (maxy - miny) * height)
        
        if 0 <= x_idx < width and 0 <= y_idx < height:
            return float(ndvi_data[y_idx, x_idx])
        
        return None
    
    def clear_cache(self, layer: Optional[str] = None):
        """Clear tile cache"""
        if layer:
            layer_dir = self.cache_dir / layer
            if layer_dir.exists():
                import shutil
                shutil.rmtree(layer_dir)
                logger.info(f"Cleared cache for layer: {layer}")
        else:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cleared entire tile cache")


class TileServer:
    """Tile server for serving map tiles"""
    
    def __init__(self, tiler: MapTiler):
        self.tiler = tiler
    
    async def get_tile(
        self,
        x: int,
        y: int,
        z: int,
        layer: str = "base"
    ) -> bytes:
        """Get tile as PNG bytes"""
        tile_image = self.tiler.load_tile(x, y, z, layer)
        
        if tile_image is None:
            tile_image = self.tiler.generate_empty_tile()
            self.tiler.save_tile(tile_image, x, y, z, layer)
        
        img_byte_arr = io.BytesIO()
        tile_image.save(img_byte_arr, format='PNG', optimize=True)
        return img_byte_arr.getvalue()


__all__ = [
    "TileCoordinate",
    "GeoUtils",
    "MapTiler",
    "TileServer"
]
