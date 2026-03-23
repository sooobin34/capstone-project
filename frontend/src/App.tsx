import { useState } from 'react'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'
import MrvPage from './pages/MrvPage'

const navItems = ['대시보드', '센서 데이터', '지도', 'MRV']

export default function App() {
  const [currentPage, setCurrentPage] = useState('대시보드')

  const renderPage = () => {
    switch (currentPage) {
      case '대시보드': return <Home />
      case '센서 데이터': return <SensorData />
      case '지도': return <MapPage />
      case 'MRV': return <MrvPage />
      default: return <Home />
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

/*아래는 메뉴3 생성까지 정상 작동
import { useState } from 'react'
import Home from './pages/Home'
import SensorData from './pages/SensorData'
import MapPage from './pages/MapPage'

const navItems = ['대시보드', '센서 데이터', '지도', 'MRV']

export default function App() {
  const [currentPage, setCurrentPage] = useState('대시보드')

  const renderPage = () => {
    switch (currentPage) {
      case '대시보드': return <Home />
      case '센서 데이터': return <SensorData />
      case '지도': return <MapPage />
      default: return <Home />
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