import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Fields from './pages/Fields'
import Weather from './pages/Weather'
import Advisor from './pages/Advisor'
import Regions from './pages/Regions'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="fields" element={<Fields />} />
          <Route path="weather" element={<Weather />} />
          <Route path="advisor" element={<Advisor />} />
          <Route path="regions" element={<Regions />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
