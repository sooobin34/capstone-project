import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'
import MrvPage from './pages/MrvPage'
import AlertPage from './pages/AlertPage'
import logo from './assets/logo_width.png'
import ValidationPage from './pages/ValidationPage'

const navItems = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Sensor Data', path: '/sensor' },
  { label: 'Map', path: '/map' },
  { label: 'Alerts', path: '/alerts' },
  { label: 'MRV', path: '/mrv' },
  { label: 'Validation', path: '/validation' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: '#fafafa' }}>
        <nav style={{
          borderBottom: '0.5px solid #e0e0e0',
          background: 'white',
          height: '60px',
          display: 'flex',
          alignItems: 'center',
        }}>
          <div style={{
            width: '100%',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <NavLink to="/map" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
              <img src={logo} alt="AquaPaddy" style={{ height: '40px', objectFit: 'contain' }} />
            </NavLink>
            <div style={{ display: 'flex', gap: '8px' }}>
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  style={({ isActive }) => ({
                    fontSize: '14px',
                    padding: '8px 18px',
                    borderRadius: '8px',
                    border: 'none',
                    cursor: 'pointer',
                    background: isActive ? '#f0f0f0' : 'transparent',
                    fontWeight: isActive ? 500 : 400,
                    color: isActive ? '#222' : '#888',
                    textDecoration: 'none',
                  })}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<MapPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/dashboard" element={<Home />} />
          <Route path="/sensor" element={<SensorData />} />
          <Route path="/alerts" element={<AlertPage />} />
          <Route path="/mrv" element={<MrvPage />} />
          <Route path="/validation" element={<ValidationPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}