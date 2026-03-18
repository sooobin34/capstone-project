import WaterLevelCard from "../components/dashboard/WaterLevelCard"
import MapCard from "../components/dashboard/MapCard"
import TrendChart from "../components/dashboard/TrendChart"
import SummaryCard from "../components/dashboard/SummaryCard"

export default function Home() {
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

/*import Header from "../components/Header"
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