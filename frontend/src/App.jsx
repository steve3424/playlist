import { Routes, Route, Link, Navigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import WelcomePage from "./pages/WelcomePage";

export default function App() {
  return (
    <div className="app-shell">
      <nav className="nav">
        <Link to="/welcome">Welcome</Link>
        <Link to="/login">Login</Link>
      </nav>

      <main className="page-content">
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/welcome" element={<WelcomePage />} />
        </Routes>
      </main>
    </div>
  );
}