import { useEffect } from 'react'
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
  return (
    <div style={{ borderRadius: '12px', overflow: 'hidden', border: '0.5px solid #e0e0e0', height: '400px' }}>
      <MapContainer center={center} zoom={15} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={center} />
       {sensors.map((sensor) => (
       <Marker key={sensor.id} position={[sensor.lat, sensor.lng]}
        eventHandlers={{
         mouseover: (e) => e.target.openPopup(),
         mouseout: (e) => e.target.closePopup(),
       }}
  >
    <Popup>{sensor.name}</Popup>
  </Marker>
))}
      </MapContainer>
    </div>
  )
}

