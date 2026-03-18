export default function SummaryCard() {
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-gray-600 font-semibold mb-4">
        MRV Summary
      </h2>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-gray-500 text-sm">AWD Cycles</p>
          <p className="text-xl font-bold mt-2">3 Times</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-gray-500 text-sm">Flooded Days</p>
          <p className="text-xl font-bold mt-2">5 Days</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-gray-500 text-sm">Dry Days</p>
          <p className="text-xl font-bold mt-2">8 Days</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-gray-500 text-sm">CO₂ Reduction</p>
          <p className="text-xl font-bold mt-2">15.8</p>
        </div>
      </div>
    </div>
  )
}