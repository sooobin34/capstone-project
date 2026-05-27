import { BrowserRouter, Routes, Route, NavLink, useLocation, Navigate } from 'react-router-dom'
import { useState, createContext, useContext } from 'react'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'
import MrvPage from './pages/MrvPage'
import AlertPage from './pages/AlertPage'
import logo from './assets/logo_width.png'
import ValidationPage from './pages/ValidationPage'

// 전역 Context 타입
interface FieldContextType {
  selectedRegion: string
  selectedFieldId: number | null
  setSelectedRegion: (region: string) => void
  setSelectedFieldId: (id: number | null) => void
}

// Context 생성 및 export (각 페이지에서 import해서 쓸 거야)
export const FieldContext = createContext<FieldContextType>({
  selectedRegion: '',
  selectedFieldId: null,
  setSelectedRegion: () => {},
  setSelectedFieldId: () => {},
})

export const useFieldContext = () => useContext(FieldContext)

const navItems = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Sensor Data', path: '/sensor' },
  { label: 'Map', path: '/map' },
  { label: 'Alerts', path: '/alerts' },
  { label: 'MRV', path: '/mrv' },
  { label: 'Validation', path: '/validations' },
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
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '22px', color: '#555', padding: '4px 8px' }}
            >
              {menuOpen ? 'Close' : 'Menu'}
            </button>
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
  const [selectedRegion, setSelectedRegion] = useState('')
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null)

  return (
    <FieldContext.Provider value={{ selectedRegion, selectedFieldId, setSelectedRegion, setSelectedFieldId }}>
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
            <Route path="/validation" element={<Navigate to="/validations" replace />} />
            <Route path="/validations" element={<ValidationPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </FieldContext.Provider>
  )
}