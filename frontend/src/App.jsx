import { Routes, Route, Link, Navigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import WelcomePage from "./pages/WelcomePage";
import PublicOnlyRoute from "./auth/PublicOnlyRoute";
import ProtectedRoute from "./auth/ProtectedRoute"
import { AuthProvider } from "./auth/AuthProvider";
import Header from "./components/Header";

export default function App() {
  return (
    <div className="app-shell">
      <main className="page-content">
        <AuthProvider>
          <Header />
          <Routes>
            <Route path="/" element={
                <Navigate to="/login" replace />
            } />
            <Route path="/login" element={
              <PublicOnlyRoute>
                <LoginPage />
              </PublicOnlyRoute>
            } />
            <Route path="/welcome" element={
              <ProtectedRoute>
                <WelcomePage />
              </ProtectedRoute>
            } />
          </Routes>
        </AuthProvider>
      </main>
    </div>
  );
}