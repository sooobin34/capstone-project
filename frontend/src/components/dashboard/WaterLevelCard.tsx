export default function WaterLevelCard() {
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-gray-500 text-sm font-medium">
        Current Water Level
      </h2>

      <div className="mt-4 flex items-end gap-2">
        <span className="text-5xl font-bold text-gray-800">12</span>
        <span className="text-lg text-gray-500">cm</span>
      </div>

      <div className="mt-4 flex items-center gap-2 text-blue-500 font-medium">
        <span>💧</span>
        <span>Status: Flooded</span>
      </div>

      <div className="mt-2 text-gray-400 text-sm">
        Last Update: 10:15 AM
      </div>
    </div>
  )
}