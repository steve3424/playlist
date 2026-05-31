import { useParams, Link } from "react-router-dom";

export default function BandPage() {
  const { bandName } = useParams();
  const decodedName = bandName ? decodeURIComponent(bandName) : "";

  return (
    <div className="container">
      <div className="login-form">
        <h1>{decodedName ? decodedName : "Band"}</h1>
        {decodedName ? (
          <p>You are viewing band: {decodedName}</p>
        ) : (
          <p>No band selected.</p>
        )}
        <Link to="/welcome">Back to bands</Link>
      </div>
    </div>
  );
}
