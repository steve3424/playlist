import { useParams, Link } from "react-router-dom";

export default function BandPage({ section }) {
  const { bandName } = useParams();
  const decodedName = bandName ? decodeURIComponent(bandName) : "";
  const sectionLabel = section ? section : "Overview";

  return (
    <div className="container">
      <div className="login-form">
        <h1>{decodedName ? decodedName : "Band"}</h1>
        {decodedName ? (
          <>
            <p>{section ? `${sectionLabel} for ${decodedName}` : `You are viewing band: ${decodedName}`}</p>
            <p>Use the navigation links above to explore this band.</p>
          </>
        ) : (
          <p>No band selected.</p>
        )}
        <Link to="/welcome">Back to bands</Link>
      </div>
    </div>
  );
}
