import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts"

const data = [
  { day: "Mon", level: 10 },
  { day: "Tue", level: 12 },
  { day: "Wed", level: 8 },
  { day: "Thu", level: 14 },
  { day: "Fri", level: 11 }
]

export default function TrendChart() {
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-gray-600 font-semibold mb-4">
        Water Level Trend
      </h2>

      <div className="w-full h-64">
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="level"
              stroke="#3b82f6"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}