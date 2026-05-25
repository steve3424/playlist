// PublicOnlyRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export default function PublicOnlyRoute({ children }) {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (authenticated) {
    return <Navigate to="/welcome" replace />;
  }

  return children;
}