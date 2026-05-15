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
  level?: number | null
  status?: string
}

interface FieldMapProps {
  sensors: Sensor[]
  center: [number, number]
  onNodeClick?: (sensor: Sensor) => void
  selectedNodeId?: number | null
}

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, 16)
  }, [center, map])
  return null
}

const createNodeIcon = (selected: boolean, level: number | null | undefined, nodeId: number) => {
  const label = level !== null && level !== undefined ? `${level > 0 ? '+' : ''}${level} cm` : '-'
  const dotColor = selected ? '#1D9E75' : '#1D9E75'
  return L.divIcon({
    className: '',
    html: `
      <div style="
        background: white;
        border-radius: 8px;
        padding: 6px 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        border: 1px solid #e0e0e0;
        position: relative;
        min-width: 70px;
        text-align: left;
      ">
        <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 2px;">
          <div style="width: 8px; height: 8px; border-radius: 50%; background: ${dotColor};"></div>
          <span style="font-size: 12px; font-weight: 600; color: #222;">Node ${nodeId}</span>
        </div>
        <span style="font-size: 12px; font-weight: 600; color: ${selected ? '#1D9E75' : '#333'};">${label}</span>
        <div style="
          position: absolute;
          bottom: -6px;
          left: 50%;
          transform: translateX(-50%);
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-top: 6px solid white;
        "></div>
      </div>
    `,
    iconSize: [80, 50],
    iconAnchor: [40, 56],
  })
}

export default function FieldMap({ sensors, center, onNodeClick, selectedNodeId }: FieldMapProps) {
  const [isSatellite, setIsSatellite] = useState(false)

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={center}
        zoom={16}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution={isSatellite
            ? 'Tiles &copy; Esri'
            : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'}
          url={isSatellite
            ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            : 'https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png'}
        />
        <MapUpdater center={center} />
        {sensors.map((sensor) => (
          <Marker
            key={sensor.id}
            position={[sensor.lat, sensor.lng]}
            icon={createNodeIcon(selectedNodeId === sensor.id, sensor.level, sensor.id)}
            eventHandlers={{
              click: () => onNodeClick?.(sensor),
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