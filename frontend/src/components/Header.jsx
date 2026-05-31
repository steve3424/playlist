import { useAuth } from "../auth/AuthProvider";
import { useNavigate, useLocation, Link, NavLink } from "react-router-dom";
import "./Header.css";

export default function Header() {
  const {user, setUser} = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isLogin = location.pathname === "/login";
  const isWelcome = location.pathname === "/welcome";
  const isBandPage = location.pathname.startsWith("/band/");

  const handleSignOut = async () => {
    console.log("logging out...")
    const response = await fetch(`http://localhost:8000/api/v1/sessions/${user}`, {
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
    <header className="app-header" role="banner">
      <div className="left">
        <Link to="/" className="app-title" aria-label="Playlist home">Playlist</Link>
        {isBandPage && (
          <nav className="nav" aria-label="Main navigation">
            <NavLink to="/songs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>songs</NavLink>
            <NavLink to="/members" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>members</NavLink>
            <NavLink to="/gigs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>gigs</NavLink>
          </nav>
        )}
      </div>

      {(isWelcome || isBandPage) && user ? (
        <button className="sign-out-button" onClick={handleSignOut} aria-label="Sign out">
          sign_out()
        </button>
      ) : null}
    </header>
  );
}
