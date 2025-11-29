import { useEffect, useState } from "react";
import {
  getSoilSummary,
  getWeatherForecast,
  getLatestNdvi,
  getFieldBoundary,
} from "../services/api";
import NDVIMap from "./NDVIMap";

export default function Dashboard() {
  const [soil, setSoil] = useState(null);
  const [weather, setWeather] = useState(null);
  const [ndvi, setNdvi] = useState(null);
  const [boundary, setBoundary] = useState(null);
  const tenant = 1;
  const field = 10;

  useEffect(() => {
    async function load() {
      try {
        const [s, w, n, b] = await Promise.all([
          getSoilSummary(tenant, field),
          getWeatherForecast(tenant, field),
          getLatestNdvi(tenant, field),
          getFieldBoundary(tenant, field),
        ]);
        setSoil(s);
        setWeather(w);
        setNdvi(n);
        setBoundary(b);
      } catch (err) {
        console.error("Error loading dashboard data", err);
      }
    }
    load();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Farmer Dashboard</h1>

      <h2>خريطة NDVI</h2>
      {ndvi && boundary ? (
        <NDVIMap
          fieldBoundary={boundary}
          ndviUrl={ndvi.ndvi_preview_png}
          imageBounds={ndvi.image_bounds}
        />
      ) : (
        <p>جار تحميل الخريطة وطبقة NDVI...</p>
      )}

      <h2>ملخص التربة</h2>
      <pre>{JSON.stringify(soil, null, 2)}</pre>

      <h2>الطقس</h2>
      <pre>{JSON.stringify(weather, null, 2)}</pre>
    </div>
  );
}
