import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface Sensor {
  id: number
  lat: number
  lng: number
  name: string
}

interface FieldMapProps {
  sensors: Sensor[]
  center: [number, number]
}

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, 15)
  }, [center, map])
  return null
}

export default function FieldMap({ sensors, center }: FieldMapProps) {
  const [isSatellite, setIsSatellite] = useState(false)

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={center}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          attribution={isSatellite
            ? 'Tiles &copy; Esri'
            : '&copy; OpenStreetMap contributors'}
          url={isSatellite
            ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
        />
        <MapUpdater center={center} />
        {sensors.map((sensor) => (
          <Marker
            key={sensor.id}
            position={[sensor.lat, sensor.lng]}
            eventHandlers={{
              mouseover: (e) => e.target.openPopup(),
              mouseout: (e) => e.target.closePopup(),
            }}
          >
            <Popup>{sensor.name}</Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* 지도/스카이뷰 전환 버튼 */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 1000,
        display: 'flex',
        background: 'white',
        borderRadius: '8px',
        border: '0.5px solid #e0e0e0',
        overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
      }}>
        {['지도', '스카이뷰'].map((label) => (
          <button
            key={label}
            onClick={() => setIsSatellite(label === '스카이뷰')}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              border: 'none',
              cursor: 'pointer',
              background: (label === '스카이뷰') === isSatellite ? '#1D9E75' : 'white',
              color: (label === '스카이뷰') === isSatellite ? 'white' : '#555',
              fontWeight: (label === '스카이뷰') === isSatellite ? 500 : 400,
            }}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}