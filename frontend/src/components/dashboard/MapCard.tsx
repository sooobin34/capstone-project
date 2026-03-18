export default function MapCard() {
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-gray-600 font-semibold mb-4">
        Field Location
      </h2>

      <div className="rounded-lg overflow-hidden">
        <img
          src="/map.jpg"
          alt="map"
          className="w-full h-48 object-cover hover:scale-105 transition"
        />
      </div>
    </div>
  )
}