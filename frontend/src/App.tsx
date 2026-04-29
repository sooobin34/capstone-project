import { useState } from 'react'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'
import MrvPage from './pages/MrvPage'
import AlertPage from './pages/AlertPage'

const navItems = ['Sensor Data', 'Map', 'Alerts', 'MRV']

export default function App() {
  const [currentPage, setCurrentPage] = useState('대시보드')

  const renderPage = () => {
  switch (currentPage) {
    case '대시보드': return <Home onNavigate={setCurrentPage} />
    case 'Sensor Data': return <SensorData />
    case 'Map': return <MapPage />
    case 'Alerts': return <AlertPage />
    case 'MRV': return <MrvPage />
    default: return <Home onNavigate={setCurrentPage} />
  }
}

  return (
    <div style={{ minHeight: '100vh', background: '#fafafa' }}>
      <nav style={{
        borderBottom: '0.5px solid #e0e0e0',
        background: 'white',
        height: '48px',
        display: 'flex',
        alignItems: 'center',
      }}>
        <div style={{
          maxWidth: '1200px',
          width: '100%',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span
            onClick={() => setCurrentPage('대시보드')}
            style={{ fontWeight: 500, fontSize: '20px', cursor: 'pointer', color: currentPage === '대시보드' ? '#1D9E75' : '#222' }}
          >
            (로고, 대시보드)
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>   
            {navItems.map((item) => (
              <button
                key={item}
                onClick={() => setCurrentPage(item)}
                style={{
                  fontSize: '13px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  background: currentPage === item ? '#f0f0f0' : 'transparent',
                  fontWeight: currentPage === item ? 500 : 400,
                  color: currentPage === item ? '#222' : '#888',
                }}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </nav>
      {renderPage()}
    </div>
  )
}

/* 아래는 대시보드를 메뉴와 분리하기 전
import { useState } from 'react'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'
import MrvPage from './pages/MrvPage'
import AlertPage from './pages/AlertPage'

const navItems = ['대시보드', '센서 데이터', '지도', '알람', 'MRV']

export default function App() {
  const [currentPage, setCurrentPage] = useState('대시보드')

  const renderPage = () => {
    switch (currentPage) {
      case '대시보드': return <Home onNavigate={setCurrentPage} />
      case '센서 데이터': return <SensorData />
      case '지도': return <MapPage />
      case '알람': return <AlertPage />
      case 'MRV': return <MrvPage />
      default: return <Home onNavigate={setCurrentPage} />
    }
  }

  return (
    <div>
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px 24px',
        borderBottom: '0.5px solid #e0e0e0',
        background: 'white',
      }}>
        <span style={{ fontWeight: 500, fontSize: '15px', marginRight: '32px' }}>논 MRV</span>
        {navItems.map((item) => (
          <button
            key={item}
            onClick={() => setCurrentPage(item)}
            style={{
              fontSize: '13px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              background: currentPage === item ? '#f0f0f0' : 'transparent',
              fontWeight: currentPage === item ? 500 : 400,
              color: currentPage === item ? '#222' : '#888',
            }}
          >
            {item}
          </button>
        ))}
      </nav>
      {renderPage()}
    </div>
  )
}
  */