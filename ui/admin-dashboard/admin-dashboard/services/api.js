
import axios from 'axios'
const GATEWAY='http://localhost:9000/api'

export async function getTenants(){
  const r=await axios.get(`${GATEWAY}/platform/api/v1/tenants`)
  return r.data
}
export async function getFields(){
  const r=await axios.get(`${GATEWAY}/platform/api/v1/fields`)
  return r.data
}
