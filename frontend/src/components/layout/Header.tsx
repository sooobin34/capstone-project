export default function Header() {
  return (
    
    <header className="sticky top-0 bg-white border-b z-50">
  <div className="max-w-6xl mx-auto flex justify-between items-center h-16 px-4">
    <h1 className="text-lg font-semibold"> ECOPaddy</h1>

    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-500">Status: Active</span>
      <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
        U
      </div>
    </div>
  </div>
</header>
  )
}
