
import { useEffect, useState } from 'react';
import { getTenants, getFields } from '../services/api';

export default function Overview(){
  const [tenants, setTenants] = useState([]);
  const [fields, setFields] = useState([]);

  useEffect(()=>{
    async function load(){
      setTenants(await getTenants());
      setFields(await getFields());
    }
    load();
  },[]);

  return (
    <div style={{padding:20}}>
      <h1>Admin Dashboard</h1>
      <h2>Tenants</h2>
      <pre>{JSON.stringify(tenants,null,2)}</pre>
      <h2>Fields</h2>
      <pre>{JSON.stringify(fields,null,2)}</pre>
    </div>
  );
}
