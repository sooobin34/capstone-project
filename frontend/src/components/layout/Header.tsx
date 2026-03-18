import { Link } from "react-router-dom"

export default function Header() {
  return (
    <header style={{ background: "#eee", padding: "10px" }}>
      <h1>My Website</h1>
      <nav>
        <Link to="/">Home</Link> |{" "}
        <Link to="/about">About</Link>
      </nav>
    </header>
  )
}