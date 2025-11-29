
import axios from 'axios';
const GATEWAY = 'http://localhost:9000/api';

export async function getSoilSummary(tenant, field) {
  const r = await axios.get(`${GATEWAY}/soil/api/v1/soil/fields/${field}/summary`, {
    params: { tenant_id: tenant }
  });
  return r.data;
}

export async function getWeatherForecast(tenant, field) {
  const r = await axios.get(`${GATEWAY}/weather/api/v1/weather/forecast`, {
    params: { tenant_id: tenant, field_id: field, hours_ahead: 48 }
  });
  return r.data;
}
