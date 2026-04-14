import React, { useEffect, useState, useRef } from "react";
import maplibregl from "maplibre-gl";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

interface Field {
  id: number;
  name: string;
  geometryType: string;
  coordinates: number[][][];
}

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [redFile, setRedFile] = useState<File | null>(null);
  const [nirFile, setNirFile] = useState<File | null>(null);
  const [threshold, setThreshold] = useState(0.4);
  const [nZones, setNZones] = useState(3);

  // Initialize map
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [45, 25],
      zoom: 5,
    });

    map.current.addControl(new maplibregl.NavigationControl(), "top-right");
    
    map.current.on("load", () => {
      loadFields();
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  const loadFields = async () => {
    try {
      const res = await fetch(`${API_BASE}/fields/`);
      const data = await res.json();
      setFields(data);
      renderFieldsOnMap(data);
    } catch (e) {
      console.error("Error loading fields:", e);
    }
  };

  const renderFieldsOnMap = (fieldsData: Field[]) => {
    if (!map.current) return;

    // Remove existing layers
    if (map.current.getLayer("fields-fill")) map.current.removeLayer("fields-fill");
    if (map.current.getLayer("fields-outline")) map.current.removeLayer("fields-outline");
    if (map.current.getSource("fields-source")) map.current.removeSource("fields-source");

    if (fieldsData.length === 0) return;

    const features = fieldsData.map((f) => ({
      type: "Feature" as const,
      geometry: {
        type: "Polygon" as const,
        coordinates: f.coordinates,
      },
      properties: { id: f.id, name: f.name },
    }));

    map.current.addSource("fields-source", {
      type: "geojson",
      data: { type: "FeatureCollection", features },
    });

    map.current.addLayer({
      id: "fields-fill",
      type: "fill",
      source: "fields-source",
      paint: {
        "fill-color": "#367C2B",
        "fill-opacity": 0.2,
      },
    });

    map.current.addLayer({
      id: "fields-outline",
      type: "line",
      source: "fields-source",
      paint: {
        "line-color": "#367C2B",
        "line-width": 2,
      },
    });
  };

  const loadZones = async (fieldId: number) => {
    if (!map.current) return;

    try {
      const res = await fetch(`${API_BASE}/fields/${fieldId}/zones`);
      const zonesData = await res.json();

      // Remove existing zones
      if (map.current.getLayer("zones-fill")) map.current.removeLayer("zones-fill");
      if (map.current.getSource("zones-source")) map.current.removeSource("zones-source");

      map.current.addSource("zones-source", {
        type: "geojson",
        data: zonesData,
      });

      map.current.addLayer({
        id: "zones-fill",
        type: "fill",
        source: "zones-source",
        paint: {
          "fill-opacity": 0.6,
          "fill-color": [
            "match",
            ["get", "level"],
            1, "#ff4444",
            2, "#ffaa00",
            3, "#44ff44",
            4, "#00aaff",
            5, "#4444ff",
            "#888888"
          ],
        },
      });
    } catch (e) {
      console.error("Error loading zones:", e);
    }
  };

  const handleUpload = async () => {
    if (!redFile || !nirFile) {
      alert("يرجى رفع ملفي B04 (Red) و B08 (NIR)");
      return;
    }

    setLoading(true);
    
    const formData = new FormData();
    formData.append("red_band", redFile);
    formData.append("nir_band", nirFile);

    try {
      const res = await fetch(
        `${API_BASE}/fields/ndvi-detect?threshold=${threshold}&n_zones=${nZones}`,
        { method: "POST", body: formData }
      );
      
      const data = await res.json();
      
      if (data.error) {
        alert(data.error);
      } else {
        alert("تم اكتشاف الحقل وإنشاء المناطق بنجاح!");
        loadFields();
      }
    } catch (e) {
      console.error("Error:", e);
      alert("حدث خطأ أثناء المعالجة");
    }
    
    setLoading(false);
  };

  const handleFieldSelect = (fieldId: number) => {
    setSelectedFieldId(fieldId);
    loadZones(fieldId);
  };

  return (
    <div className="app-container">
      <div className="map-container">
        <div id="map" ref={mapContainer} />
        
        <div className="legend">
          <h4>مستويات NDVI</h4>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "#ff4444" }} />
            <span>منخفض جداً</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "#ffaa00" }} />
            <span>منخفض</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "#44ff44" }} />
            <span>متوسط</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "#00aaff" }} />
            <span>جيد</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "#4444ff" }} />
            <span>ممتاز</span>
          </div>
        </div>
      </div>

      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>🌾 Field Suite NDVI</h1>
          <p>تحليل صحة المحاصيل</p>
        </div>

        <div className="sidebar-content">
          <div className="upload-section">
            <h3>رفع صور Sentinel-2</h3>
            
            <div className="file-input">
              <label>B04 (Red Band):</label>
              <input
                type="file"
                accept=".tif,.jp2"
                onChange={(e) => setRedFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="file-input">
              <label>B08 (NIR Band):</label>
              <input
                type="file"
                accept=".tif,.jp2"
                onChange={(e) => setNirFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="threshold-slider">
              <label>عتبة NDVI: {threshold.toFixed(2)}</label>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
              />
            </div>

            <div className="threshold-slider">
              <label>عدد المناطق: {nZones}</label>
              <input
                type="range"
                min="2"
                max="5"
                step="1"
                value={nZones}
                onChange={(e) => setNZones(parseInt(e.target.value))}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={loading}
              style={{ width: "100%", marginTop: 15 }}
            >
              {loading ? "جاري المعالجة..." : "تحليل NDVI"}
            </button>
          </div>

          <div className="field-list">
            <h3>الحقول المكتشفة ({fields.length})</h3>
            {fields.map((field) => (
              <div
                key={field.id}
                className={`field-item ${selectedFieldId === field.id ? "selected" : ""}`}
                onClick={() => handleFieldSelect(field.id)}
              >
                <strong>#{field.id}</strong> - {field.name}
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
