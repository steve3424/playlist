import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export default function LoginPage() {
  const navigate = useNavigate();
  const [user_name, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showError, setShowError] = useState(false);
  const { setUser } = useAuth();

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      console.log("logging in...")
      const response = await fetch('http://localhost/api/v1/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        credentials: 'include',
        body: new URLSearchParams({
          user_name,
          password,
        })
      });

      const result = await response.json();
      if (!response.ok) {
        console.log("logging in error")
        throw new Error(result.message || 'Login failed');
      }
      setUser(result.name);
      // navigate("/welcome");
    } catch (error) {
      console.log('Error: ', error);
      // Trigger error animation
      setShowError(true);
      // Remove animation class after animation completes (2s is the fade duration)
      setTimeout(() => setShowError(false), 2000);
    }
  };

  return (
    <div className="container">
      <form className={`login-form ${showError ? 'error' : ''}`} onSubmit={handleSubmit}>
        <h1>Login</h1>

        <input
          type="text"
          placeholder="Username"
          value={user_name}
          onChange={(event) => setUsername(event.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button type="submit">Sign In</button>
      </form>
    </div>
  );
}