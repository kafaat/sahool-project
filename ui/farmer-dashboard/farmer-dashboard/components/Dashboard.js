
import { useEffect, useState } from 'react';
import { getSoilSummary, getWeatherForecast } from '../services/api';

export default function Dashboard() {
  const [soil, setSoil] = useState(null);
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    async function load() {
      const s = await getSoilSummary(1, 10);
      const w = await getWeatherForecast(1, 10);
      setSoil(s);
      setWeather(w);
    }
    load();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Farmer Dashboard</h1>

      <h2>Soil Summary</h2>
      <pre>{JSON.stringify(soil, null, 2)}</pre>

      <h2>Weather Forecast</h2>
      <pre>{JSON.stringify(weather, null, 2)}</pre>
    </div>
  );
}
