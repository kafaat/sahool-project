import { MapContainer, TileLayer, ImageOverlay, Polygon } from "react-leaflet";

export default function NDVIMap({ fieldBoundary, ndviUrl, imageBounds }) {
  if (!fieldBoundary || !fieldBoundary.center || !fieldBoundary.vertices) {
    return <p>جارٍ تحميل حدود الحقل...</p>;
  }
  if (!ndviUrl || !imageBounds) {
    return <p>جارٍ تحميل طبقة NDVI...</p>;
  }

  return (
    <div style={{ height: "500px", width: "100%", marginTop: 20 }}>
      <MapContainer
        center={[fieldBoundary.center.lat, fieldBoundary.center.lng]}
        zoom={16}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <ImageOverlay url={ndviUrl} bounds={imageBounds} opacity={0.6} />

        <Polygon positions={fieldBoundary.vertices} pathOptions={{ color: "yellow", weight: 3 }} />
      </MapContainer>
    </div>
  );
}
