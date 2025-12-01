"""
Enhanced Input Validation
منع الأخطاء من خلال التحقق الشامل من المدخلات
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field, root_validator
from datetime import datetime, date
import re
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.validation import explain_validity

from shared.error_handling import ValidationException, SpatialDataException, ErrorDetail

# ===================================================================
# GEOMETRY VALIDATORS
# ===================================================================

class GeometryValidator:
    """Comprehensive geometry validation"""

    @staticmethod
    def validate_geojson(geojson: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GeoJSON structure and content"""

        errors = []

        # Check required fields
        if "type" not in geojson:
            errors.append(ErrorDetail(
                field="geometry.type",
                message="حقل 'type' مطلوب في GeoJSON",
                code="MISSING_FIELD"
            ))

        if "coordinates" not in geojson:
            errors.append(ErrorDetail(
                field="geometry.coordinates",
                message="حقل 'coordinates' مطلوب في GeoJSON",
                code="MISSING_FIELD"
            ))

        if errors:
            raise SpatialDataException(
                message_ar="بنية GeoJSON غير صحيحة",
                message_en="Invalid GeoJSON structure",
                details=errors
            )

        # Validate geometry type
        valid_types = ["Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"]
        if geojson["type"] not in valid_types:
            raise SpatialDataException(
                message_ar=f"نوع الهندسة '{geojson['type']}' غير مدعوم",
                message_en=f"Geometry type '{geojson['type']}' not supported",
                details=[ErrorDetail(
                    field="geometry.type",
                    message=f"يجب أن يكون أحد: {', '.join(valid_types)}",
                    code="INVALID_TYPE"
                )]
            )

        # Create Shapely geometry
        try:
            geom = shape(geojson)
        except Exception as e:
            raise SpatialDataException(
                message_ar="فشل تحويل GeoJSON إلى كائن هندسي",
                message_en="Failed to convert GeoJSON to geometry",
                details=[ErrorDetail(
                    field="geometry",
                    message=str(e),
                    code="CONVERSION_ERROR"
                )]
            )

        # Validate geometry
        if not geom.is_valid:
            reason = explain_validity(geom)
            raise SpatialDataException(
                message_ar=f"الشكل الهندسي غير صحيح: {reason}",
                message_en=f"Invalid geometry: {reason}",
                details=[ErrorDetail(
                    field="geometry",
                    message=reason,
                    code="INVALID_GEOMETRY"
                )]
            )

        # Check for empty geometry
        if geom.is_empty:
            raise SpatialDataException(
                message_ar="الشكل الهندسي فارغ",
                message_en="Geometry is empty",
                details=[ErrorDetail(
                    field="geometry",
                    message="Geometry contains no coordinates",
                    code="EMPTY_GEOMETRY"
                )]
            )

        # Validate complexity (number of vertices)
        num_coords = len(geom.coords) if hasattr(geom, 'coords') else sum(len(g.coords) for g in geom.geoms if hasattr(g, 'coords'))

        if num_coords < 3 and geojson["type"] in ["Polygon", "MultiPolygon"]:
            raise SpatialDataException(
                message_ar="المضلع يجب أن يحتوي على 3 نقاط على الأقل",
                message_en="Polygon must have at least 3 points",
                details=[ErrorDetail(
                    field="geometry",
                    message=f"Found {num_coords} points, minimum is 3",
                    code="TOO_FEW_POINTS"
                )]
            )

        if num_coords > 1000:
            raise SpatialDataException(
                message_ar=f"الشكل الهندسي معقد جداً ({num_coords} نقطة). الحد الأقصى 1000",
                message_en=f"Geometry too complex ({num_coords} points). Maximum is 1000",
                details=[ErrorDetail(
                    field="geometry",
                    message="Reduce geometry complexity by simplifying",
                    code="TOO_COMPLEX"
                )]
            )

        # Validate area for polygons
        if geojson["type"] in ["Polygon", "MultiPolygon"]:
            # Calculate area in hectares (approximate)
            area_m2 = geom.area * 111000 * 111000  # Rough conversion
            area_ha = area_m2 / 10000

            if area_ha > 10000:  # 100 km²
                raise SpatialDataException(
                    message_ar=f"مساحة الحقل كبيرة جداً ({area_ha:.0f} هكتار). الحد الأقصى 10,000 هكتار",
                    message_en=f"Field area too large ({area_ha:.0f} hectares). Maximum is 10,000 hectares",
                    details=[ErrorDetail(
                        field="geometry",
                        message="Reduce field size or split into multiple fields",
                        code="AREA_TOO_LARGE"
                    )]
                )

            if area_ha < 0.01:  # 100 m²
                raise SpatialDataException(
                    message_ar=f"مساحة الحقل صغيرة جداً ({area_ha:.4f} هكتار). الحد الأدنى 0.01 هكتار",
                    message_en=f"Field area too small ({area_ha:.4f} hectares). Minimum is 0.01 hectares",
                    details=[ErrorDetail(
                        field="geometry",
                        message="Increase field size",
                        code="AREA_TOO_SMALL"
                    )]
                )

        # Validate coordinate ranges
        bounds = geom.bounds  # (minx, miny, maxx, maxy)

        if not (-180 <= bounds[0] <= 180 and -180 <= bounds[2] <= 180):
            raise SpatialDataException(
                message_ar="خط الطول خارج النطاق المسموح (-180 إلى 180)",
                message_en="Longitude out of range (-180 to 180)",
                details=[ErrorDetail(
                    field="geometry.coordinates",
                    message=f"Longitude range: {bounds[0]:.4f} to {bounds[2]:.4f}",
                    code="INVALID_LONGITUDE"
                )]
            )

        if not (-90 <= bounds[1] <= 90 and -90 <= bounds[3] <= 90):
            raise SpatialDataException(
                message_ar="خط العرض خارج النطاق المسموح (-90 إلى 90)",
                message_en="Latitude out of range (-90 to 90)",
                details=[ErrorDetail(
                    field="geometry.coordinates",
                    message=f"Latitude range: {bounds[1]:.4f} to {bounds[3]:.4f}",
                    code="INVALID_LATITUDE"
                )]
            )

        return geojson


# ===================================================================
# FIELD VALIDATORS
# ===================================================================

class FieldValidators:
    """Validators for field-related data"""

    @staticmethod
    def validate_crop_type(crop: str) -> str:
        """Validate crop type"""

        # Allowed crop types
        valid_crops = [
            "tomato", "potato", "wheat", "corn", "rice", "cucumber",
            "pepper", "eggplant", "onion", "garlic", "lettuce", "spinach",
            "carrot", "beans", "peas", "watermelon", "melon", "strawberry",
            "date_palm", "olive", "citrus", "grape", "apple", "other"
        ]

        crop_lower = crop.lower().strip()

        if crop_lower not in valid_crops:
            raise ValidationException(
                message_ar=f"نوع المحصول '{crop}' غير مدعوم",
                message_en=f"Crop type '{crop}' not supported",
                details=[ErrorDetail(
                    field="crop",
                    message=f"Allowed crops: {', '.join(valid_crops[:10])}...",
                    code="INVALID_CROP_TYPE"
                )]
            )

        return crop_lower

    @staticmethod
    def validate_field_name(name: str) -> str:
        """Validate field name"""

        if not name or len(name.strip()) == 0:
            raise ValidationException(
                message_ar="اسم الحقل مطلوب",
                message_en="Field name is required",
                details=[ErrorDetail(
                    field="name",
                    message="Name cannot be empty",
                    code="EMPTY_NAME"
                )]
            )

        if len(name) > 255:
            raise ValidationException(
                message_ar="اسم الحقل طويل جداً (الحد الأقصى 255 حرف)",
                message_en="Field name too long (max 255 characters)",
                details=[ErrorDetail(
                    field="name",
                    message=f"Current length: {len(name)}",
                    code="NAME_TOO_LONG"
                )]
            )

        # Check for invalid characters
        if re.search(r'[<>\'\"\\]', name):
            raise ValidationException(
                message_ar="اسم الحقل يحتوي على أحرف غير مسموحة",
                message_en="Field name contains invalid characters",
                details=[ErrorDetail(
                    field="name",
                    message="Avoid special characters: < > ' \" \\",
                    code="INVALID_CHARACTERS"
                )]
            )

        return name.strip()


# ===================================================================
# DATE & TIME VALIDATORS
# ===================================================================

class DateTimeValidators:
    """Validators for date and time fields"""

    @staticmethod
    def validate_date_range(start_date: date, end_date: date, max_days: int = 365) -> tuple:
        """Validate date range"""

        errors = []

        # Check if start is before end
        if start_date > end_date:
            errors.append(ErrorDetail(
                field="date_range",
                message="تاريخ البداية يجب أن يكون قبل تاريخ النهاية",
                code="INVALID_DATE_RANGE"
            ))

        # Check if dates are not in future
        today = date.today()
        if start_date > today:
            errors.append(ErrorDetail(
                field="start_date",
                message="تاريخ البداية لا يمكن أن يكون في المستقبل",
                code="FUTURE_DATE"
            ))

        if end_date > today:
            errors.append(ErrorDetail(
                field="end_date",
                message="تاريخ النهاية لا يمكن أن يكون في المستقبل",
                code="FUTURE_DATE"
            ))

        # Check range is not too large
        days_diff = (end_date - start_date).days
        if days_diff > max_days:
            errors.append(ErrorDetail(
                field="date_range",
                message=f"الفترة طويلة جداً ({days_diff} يوم). الحد الأقصى {max_days} يوم",
                code="RANGE_TOO_LARGE"
            ))

        if errors:
            raise ValidationException(
                message_ar="خطأ في نطاق التاريخ",
                message_en="Invalid date range",
                details=errors
            )

        return start_date, end_date


# ===================================================================
# NUMERIC VALIDATORS
# ===================================================================

class NumericValidators:
    """Validators for numeric fields"""

    @staticmethod
    def validate_positive(value: float, field_name: str) -> float:
        """Validate that value is positive"""

        if value <= 0:
            raise ValidationException(
                message_ar=f"{field_name} يجب أن يكون أكبر من صفر",
                message_en=f"{field_name} must be greater than zero",
                details=[ErrorDetail(
                    field=field_name,
                    message=f"Current value: {value}",
                    code="NOT_POSITIVE"
                )]
            )

        return value

    @staticmethod
    def validate_percentage(value: float, field_name: str) -> float:
        """Validate percentage (0-100)"""

        if not (0 <= value <= 100):
            raise ValidationException(
                message_ar=f"{field_name} يجب أن يكون بين 0 و 100",
                message_en=f"{field_name} must be between 0 and 100",
                details=[ErrorDetail(
                    field=field_name,
                    message=f"Current value: {value}",
                    code="OUT_OF_RANGE"
                )]
            )

        return value

    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> float:
        """Validate value is within range"""

        if not (min_val <= value <= max_val):
            raise ValidationException(
                message_ar=f"{field_name} يجب أن يكون بين {min_val} و {max_val}",
                message_en=f"{field_name} must be between {min_val} and {max_val}",
                details=[ErrorDetail(
                    field=field_name,
                    message=f"Current value: {value}",
                    code="OUT_OF_RANGE"
                )]
            )

        return value


# ===================================================================
# PAGINATION VALIDATORS
# ===================================================================

class PaginationValidator:
    """Validate pagination parameters"""

    @staticmethod
    def validate(page: int, page_size: int, max_page_size: int = 1000) -> tuple:
        """Validate pagination parameters"""

        errors = []

        if page < 1:
            errors.append(ErrorDetail(
                field="page",
                message="رقم الصفحة يجب أن يكون 1 أو أكبر",
                code="INVALID_PAGE"
            ))

        if page_size < 1:
            errors.append(ErrorDetail(
                field="page_size",
                message="حجم الصفحة يجب أن يكون 1 أو أكبر",
                code="INVALID_PAGE_SIZE"
            ))

        if page_size > max_page_size:
            errors.append(ErrorDetail(
                field="page_size",
                message=f"حجم الصفحة كبير جداً. الحد الأقصى {max_page_size}",
                code="PAGE_SIZE_TOO_LARGE"
            ))

        if errors:
            raise ValidationException(
                message_ar="خطأ في معاملات الصفحات",
                message_en="Invalid pagination parameters",
                details=errors
            )

        return page, page_size


# ===================================================================
# PYDANTIC MODELS WITH VALIDATION
# ===================================================================

class ValidatedFieldCreate(BaseModel):
    """Field creation with validation"""

    name: str = Field(..., min_length=1, max_length=255)
    crop: Optional[str] = None
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    tenant_id: str

    @validator('name')
    def validate_name(cls, v):
        return FieldValidators.validate_field_name(v)

    @validator('crop')
    def validate_crop(cls, v):
        if v:
            return FieldValidators.validate_crop_type(v)
        return v

    @validator('geometry')
    def validate_geometry(cls, v):
        return GeometryValidator.validate_geojson(v)

    class Config:
        schema_extra = {
            "example": {
                "name": "حقل الطماطم الشمالي",
                "crop": "tomato",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[30.0, 31.0], [30.1, 31.0], [30.1, 31.1], [30.0, 31.1], [30.0, 31.0]]]
                },
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ValidatedSpatialQuery(BaseModel):
    """Spatial query with validation"""

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    distance: float = Field(..., gt=0, le=100000, description="Distance in meters")
    limit: int = Field(default=10, ge=1, le=100)

    class Config:
        schema_extra = {
            "example": {
                "lat": 30.0,
                "lon": 31.0,
                "distance": 5000,
                "limit": 10
            }
        }


# ===================================================================
# USAGE EXAMPLES
# ===================================================================

"""
# In API routes:

from shared.validation import ValidatedFieldCreate, ValidatedSpatialQuery

@router.post("/fields")
async def create_field(field_data: ValidatedFieldCreate):
    # Validation happens automatically via Pydantic
    # If validation fails, FastAPI returns 422 with error details
    ...

@router.get("/fields/nearby")
async def nearby_fields(query: ValidatedSpatialQuery = Depends()):
    # Query parameters validated automatically
    ...


# Manual validation:

from shared.validation import GeometryValidator

geometry = request.json()["geometry"]
GeometryValidator.validate_geojson(geometry)  # Raises SpatialDataException if invalid
"""
