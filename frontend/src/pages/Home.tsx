import WaterLevelCard from "../components/dashboard/WaterLevelCard"
import MapCard from "../components/dashboard/MapCard"
import TrendChart from "../components/dashboard/TrendChart"
import SummaryCard from "../components/dashboard/SummaryCard"

export default function Home() {
  return (
    <div className="bg-gray-100 min-h-screen">
      
      <div className="p-6">

        {/* 메인 카드 영역 */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">

          <WaterLevelCard />
          <MapCard />

          <TrendChart />
          <SummaryCard />

        </div>

        {/* 센서 카드 영역 */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          
          <div className="bg-white p-4 rounded-xl shadow">
            <h2 className="text-sm text-gray-500">Temperature</h2>
            <p className="text-2xl font-semibold mt-2">25°C</p>
          </div>

          <div className="bg-white p-4 rounded-xl shadow">
            <h2 className="text-sm text-gray-500">Humidity</h2>
            <p className="text-2xl font-semibold mt-2">60%</p>
          </div>

          <div className="bg-white p-4 rounded-xl shadow">
            <h2 className="text-sm text-gray-500">Soil</h2>
            <p className="text-2xl font-semibold mt-2">Good</p>
          </div>

        </div>

      </div>

    </div>
  )
}

/*export default function Home() {
  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="grid grid-cols-2 gap-6">
        <WaterLevelCard />
        <MapCard />
        <TrendChart />
        <SummaryCard />
      </div>
    </div>
  )
}

이 아래는 진짜 주석
import Header from "../components/Header"
import Footer from "../components/Footer"

export default function Home() {
  return (
    <div>
      <Header />

      <main style={{ padding: "20px" }}>
  <div>내 웹 시작</div>
</main>

      <Footer />
    </div>
  )
} 갑자기 헤더 푸터 필요없다고 수정하기 전 잘 돌아가는 코드 */ 