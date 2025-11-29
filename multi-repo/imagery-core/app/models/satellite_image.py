from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base import Base

class SatelliteImage(Base):
    __tablename__ = "satellite_images"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True)
    field_id = Column(Integer, index=True)
    scene_id = Column(String, index=True)
    product_name = Column(String)
    timestamp = Column(DateTime)
    cloudcover = Column(Float)
    ndvi_path = Column(String)  # path or URL to NDVI preview
    raw_zip = Column(String)

    @property
    def ndvi_preview_png(self):
        # هنا نفترض أن ndvi_path هو URL جاهز؛ يمكن تعديلها لاحقاً
        return self.ndvi_path

    @property
    def image_bounds(self):
        # يمكن لاحقاً تخزين bounds في جدول مستقل
        return None
