import { useAuth } from "../auth/AuthProvider";
import { useNavigate, useLocation } from "react-router-dom";
import "./Header.css";

export default function Header() {
  const {user, setUser} = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Don't show header on login page or
  // if user is logged in.
  if (location.pathname === "/login" || !user ) {
    return null;
  }

  const handleSignOut = async () => {
    console.log("logging out...")
    const response = await fetch(`http://localhost/api/v1/sessions/${user}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      console.log("Log out error!")
      throw new Error(result.message || 'Logout failed');
    }

    console.log("setting user...")
    setUser(null);
    console.log("navigating...")
    // navigate("/login");
  };

  return (
    <header className="app-header">
      <button className="sign-out-button" onClick={handleSignOut}>
        sign_out()
      </button>
    </header>
  );
}
