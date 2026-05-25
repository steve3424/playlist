// PublicOnlyRoute.jsx
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export default function PublicOnlyRoute({ children }) {
  const { user, authenticated, isLoading } = useAuth();
  const location = useLocation();
  console.log("%s authenticated: %s", location.pathname, authenticated)
  console.log("%s isLoading: %s", location.pathname, isLoading)
  console.log("%s user: %s", location.pathname, user)

  if (isLoading) {
    return null; // or return a loading spinner component
  }

  if (authenticated) {
    return <Navigate to="/welcome"/>;
  }

  return children;
}