
/*import { Link, useLocation } from "react-router-dom";

export default function Sidebar() {
  const location = useLocation();

  // 스케치에 있던 메뉴들을 구성합니다.
  const menus = [
    { name: "대시보드", path: "/" },
    { name: "지도/위치", path: "/map" },
    { name: "알림 내역", path: "/alerts" },
    { name: "MRV 보고서", path: "/reports" },
  ];

  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4 flex flex-col">
      <div className="text-xl font-bold mb-8 px-2 text-green-400">
        🌱 Carbon MRV
      </div>
      
      <nav className="flex-1">
        {menus.map((menu) => (
          <Link
            key={menu.name}
            to={menu.path}
            className={`block px-4 py-3 mb-2 rounded-lg transition-colors ${
              location.pathname === menu.path
                ? "bg-green-600 text-white" // 현재 선택된 메뉴 색상
                : "text-gray-400 hover:bg-gray-800 hover:text-white"
            }`}
          >
            {menu.name}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700 text-sm text-gray-500">
        팀장님 이름 (Admin)
      </div>
    </div>
  );
}
  */