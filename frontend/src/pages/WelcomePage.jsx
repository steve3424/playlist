import { useAuth } from "../auth/AuthProvider";
import { useEffect, useState } from "react";

export default function WelcomePage() {
  const {user} = useAuth();
  const [bands, setBands] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBands() {
      try {
        // TODO: Replace this placeholder request with your real bands endpoint
        const response = await fetch(`http://localhost:8000/api/v1/bands`, {
          method: "GET",
          credentials: "include",
        });
        const data = await response.json()

        const bands = data.map(band => band.name) || [];
        setBands(bands);
      } catch (error) {
        console.error("Failed to load bands", error);
        setBands([]);
      } finally {
        setLoading(false);
      }
    }

    fetchBands();
  }, []);

  return (
    <div className="container">
      <div className="login-form">
        <h1>Welcome{user ? `, ${user}!` : ""}</h1>
        {loading ? (
          <p>Loading your bands…</p>
        ) : bands.length > 0 ? (
          <>
            <p>Here are the bands you are currently a member of:</p>
            <ul className="band-list">
              {bands.map((band) => (
                <li key={band} className="band-item">
                  <button
                    type="button"
                    className="band-button"
                    onClick={() => {
                      // TODO: navigate to the band page when ready
                    }}
                  >
                    {band}
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <>
            <p>You are not currently a member of any bands.</p>
            <button type="button">Join a band</button>
          </>
        )}
      </div>
    </div>
  );
}
