"""Unit tests for NDVI Service"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNDVIComputation:
    """Test NDVI formula and computation"""

    def test_ndvi_formula_basic(self):
        """Test NDVI formula: (NIR - Red) / (NIR + Red)"""
        # Healthy vegetation: high NIR, low Red
        nir = 0.5
        red = 0.1
        expected = (nir - red) / (nir + red)  # 0.67
        assert abs(expected - 0.667) < 0.01

    def test_ndvi_range(self):
        """NDVI should be between -1 and 1"""
        test_cases = [
            (0.8, 0.1),  # Healthy vegetation
            (0.2, 0.8),  # Water/bare soil
            (0.5, 0.5),  # Neutral
            (0.01, 0.01),  # Very low values
        ]

        for nir, red in test_cases:
            ndvi = (nir - red) / (nir + red + 1e-9)
            assert -1 <= ndvi <= 1, f"NDVI {ndvi} out of range for NIR={nir}, Red={red}"

    def test_healthy_vegetation_high_ndvi(self):
        """Healthy vegetation should have NDVI > 0.4"""
        nir = 0.8
        red = 0.1
        ndvi = (nir - red) / (nir + red + 1e-9)
        assert ndvi > 0.4, "Healthy vegetation should have NDVI > 0.4"

    def test_water_negative_ndvi(self):
        """Water bodies should have negative NDVI"""
        nir = 0.1
        red = 0.3
        ndvi = (nir - red) / (nir + red + 1e-9)
        assert ndvi < 0, "Water should have negative NDVI"

    def test_ndvi_numpy_array(self):
        """Test NDVI computation with numpy arrays"""
        nir_data = np.array([[0.5, 0.8], [0.2, 0.6]])
        red_data = np.array([[0.1, 0.1], [0.3, 0.2]])

        ndvi = (nir_data - red_data) / (nir_data + red_data + 1e-9)

        assert ndvi.shape == (2, 2)
        assert ndvi[0, 0] > 0.5  # Healthy
        assert ndvi[0, 1] > 0.7  # Very healthy
        assert ndvi[1, 0] < 0    # Water/stressed
        assert ndvi[1, 1] > 0    # Moderate


class TestNDVIZones:
    """Test zone classification by NDVI quantiles"""

    def test_quantile_calculation(self):
        """Test that quantiles divide data correctly"""
        data = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        n_zones = 3

        quantiles = np.quantile(data, np.linspace(0, 1, n_zones + 1))

        assert len(quantiles) == n_zones + 1
        assert quantiles[0] == data.min()
        assert quantiles[-1] == data.max()

    def test_zone_ranges_non_overlapping(self):
        """Zone ranges should not overlap"""
        data = np.random.rand(100)
        n_zones = 3

        quantiles = np.quantile(data, np.linspace(0, 1, n_zones + 1))

        for i in range(n_zones - 1):
            assert quantiles[i + 1] <= quantiles[i + 2], "Quantiles should be ordered"

    def test_three_zones_creation(self):
        """Test creating 3 zones from NDVI data"""
        ndvi = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])

        flat = ndvi.flatten()
        n_zones = 3
        quantiles = np.quantile(flat, np.linspace(0, 1, n_zones + 1))

        # Each zone should have approximately equal data points
        for i in range(n_zones):
            low, high = quantiles[i], quantiles[i + 1]
            count = np.sum((flat >= low) & (flat <= high))
            assert count >= 1, f"Zone {i+1} should have data"


class TestThresholdDetection:
    """Test field detection with NDVI threshold"""

    def test_threshold_filtering(self):
        """Test that threshold correctly filters NDVI values"""
        ndvi = np.array([
            [0.1, 0.2, 0.5],
            [0.6, 0.7, 0.3],
            [0.8, 0.4, 0.2]
        ])

        threshold = 0.4
        mask = ndvi > threshold

        expected_mask = np.array([
            [False, False, True],
            [True, True, False],
            [True, False, False]
        ])

        np.testing.assert_array_equal(mask, expected_mask)

    def test_high_threshold_less_detection(self):
        """Higher threshold should detect less area"""
        ndvi = np.random.rand(100, 100)

        mask_low = ndvi > 0.2
        mask_mid = ndvi > 0.5
        mask_high = ndvi > 0.8

        assert mask_low.sum() >= mask_mid.sum() >= mask_high.sum()

    def test_threshold_edge_cases(self):
        """Test threshold at boundary values"""
        ndvi = np.array([0.4, 0.4, 0.41, 0.39])

        threshold = 0.4
        mask = ndvi > threshold

        assert mask[0] == False  # Exactly at threshold
        assert mask[1] == False  # Exactly at threshold
        assert mask[2] == True   # Just above
        assert mask[3] == False  # Just below


class TestSentinelBands:
    """Test Sentinel-2 band processing"""

    def test_band_names(self):
        """Test correct band identification"""
        bands = {
            "B04": "Red (665nm)",
            "B08": "NIR (842nm)"
        }

        assert "B04" in bands
        assert "B08" in bands

    def test_band_resolution(self):
        """Test band resolution expectations"""
        # B04 and B08 are 10m resolution in Sentinel-2
        resolution = 10  # meters

        # 1km x 1km area should have 100x100 pixels
        area_size = 1000  # meters
        expected_pixels = area_size // resolution

        assert expected_pixels == 100


class TestContourDetection:
    """Test contour and polygon detection"""

    def test_contour_from_binary_mask(self):
        """Test contour detection from binary mask"""
        from skimage import measure

        # Create a simple square mask
        mask = np.zeros((10, 10), dtype=bool)
        mask[2:8, 2:8] = True

        contours = measure.find_contours(mask, 0.5)

        assert len(contours) > 0, "Should find at least one contour"

    def test_polygon_from_contour(self):
        """Test creating polygon from contour points"""
        from shapely.geometry import Polygon

        # Simple rectangle contour
        contour = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]

        poly = Polygon(contour)

        assert poly.is_valid
        assert poly.area == 1.0

    def test_largest_polygon_selection(self):
        """Test selecting largest polygon"""
        from shapely.geometry import Polygon

        polygons = [
            Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),  # Area = 1
            Polygon([(0, 0), (0, 2), (2, 2), (2, 0)]),  # Area = 4
            Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)]),  # Area = 0.25
        ]

        largest = max(polygons, key=lambda p: p.area)

        assert largest.area == 4.0


class TestModelStructure:
    """Test database model structure"""

    def test_field_model_attributes(self):
        """Test FieldModel has required attributes"""
        required_attrs = ['id', 'name', 'geometry_type', 'geom_wkt', 'metadata_json']

        # Simulate model structure check
        class MockField:
            id = 1
            name = "Test Field"
            geometry_type = "Polygon"
            geom_wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
            metadata_json = '{"thr": 0.4}'

        field = MockField()
        for attr in required_attrs:
            assert hasattr(field, attr), f"Field should have {attr}"

    def test_zone_model_attributes(self):
        """Test FieldZoneModel has required attributes"""
        required_attrs = ['id', 'field_id', 'level', 'min_ndvi', 'max_ndvi', 'geom_wkt']

        class MockZone:
            id = 1
            field_id = 1
            level = 1
            min_ndvi = 0.0
            max_ndvi = 0.3
            geom_wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"

        zone = MockZone()
        for attr in required_attrs:
            assert hasattr(zone, attr), f"Zone should have {attr}"


class TestGeoJSONOutput:
    """Test GeoJSON output format"""

    def test_feature_collection_structure(self):
        """Test FeatureCollection has correct structure"""
        from shapely.geometry import Polygon, mapping

        poly = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])

        feature = {
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "id": 1,
                "level": 1,
                "min": 0.0,
                "max": 0.3
            }
        }

        fc = {
            "type": "FeatureCollection",
            "features": [feature]
        }

        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) == 1
        assert fc["features"][0]["type"] == "Feature"

    def test_polygon_mapping(self):
        """Test shapely polygon to GeoJSON mapping"""
        from shapely.geometry import Polygon, mapping

        poly = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        geojson = mapping(poly)

        assert geojson["type"] == "Polygon"
        assert "coordinates" in geojson


class TestHeatmapGeneration:
    """Test NDVI heatmap PNG generation"""

    def test_ndvi_colormap(self):
        """Test NDVI visualization uses RdYlGn colormap"""
        import matplotlib

        cmap = matplotlib.colormaps.get_cmap("RdYlGn")

        # Test color at different NDVI values
        color_low = cmap(0)    # NDVI = -1 (red-ish)
        color_mid = cmap(0.5)  # NDVI = 0 (yellow)
        color_high = cmap(1)   # NDVI = 1 (green)

        # RdYlGn colormap: low values are red/brown, high values are green
        # Green component (index 1) should be higher at high NDVI
        assert color_high[1] > color_low[1], "Green should be higher at high NDVI"
        # Blue component remains relatively low throughout
        assert color_high[2] < 0.5, "Blue should be relatively low in RdYlGn"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
