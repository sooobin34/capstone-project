import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'
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

function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const isMobile = window.innerWidth <= 768

  return (
    <nav style={{
      borderBottom: '0.5px solid #e0e0e0',
      background: 'white',
      height: '48px',
      display: 'flex',
      alignItems: 'center',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{
        width: '100%',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <NavLink to="/map" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
          <img src={logo} alt="AquaPaddy" style={{ height: '44px', objectFit: 'contain' }} />
        </NavLink>

        {isMobile ? (
          <>
            {/* 햄버거 버튼 */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '22px', color: '#555', padding: '4px 8px' }}
            >
              {menuOpen ? '✕' : '☰'}
            </button>

            {/* 모바일 드롭다운 메뉴 */}
            {menuOpen && (
              <div style={{
                position: 'fixed', top: '48px', left: 0, right: 0,
                background: 'white', borderBottom: '0.5px solid #e0e0e0',
                zIndex: 200, padding: '8px 0',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              }}>
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMenuOpen(false)}
                    style={({ isActive }) => ({
                      display: 'block',
                      padding: '12px 20px',
                      fontSize: '14px',
                      fontWeight: isActive ? 500 : 400,
                      color: isActive ? '#1D9E75' : '#555',
                      textDecoration: 'none',
                      background: isActive ? '#f0faf6' : 'white',
                      borderLeft: isActive ? '3px solid #1D9E75' : '3px solid transparent',
                    })}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            )}
          </>
        ) : (
          <div style={{ display: 'flex', gap: '4px' }}>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  fontSize: '13px',
                  padding: '6px 14px',
                  borderRadius: '8px',
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
        )}
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: '#fafafa' }}>
        <NavBar />
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