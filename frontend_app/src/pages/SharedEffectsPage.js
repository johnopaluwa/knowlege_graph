import { useEffect, useState } from "react";
import "./Pages.css"; // Shared CSS for pages

const SharedEffectsPage = () => {
  const [sharedEffects, setSharedEffects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const sharedEffectsResponse = await fetch(
          "http://localhost:5000/shared_effects"
        );
        if (!sharedEffectsResponse.ok) {
          throw new Error(
            `HTTP error! status: ${sharedEffectsResponse.status}`
          );
        }
        const sharedEffectsData = await sharedEffectsResponse.json();
        setSharedEffects(sharedEffectsData);
      } catch (error) {
        setError(error);
        console.error("Error fetching shared effects data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return <div className="page-message">Loading shared effects...</div>;
  }

  if (error) {
    return (
      <div className="page-message error">
        Error: {error.message}. Make sure the Flask API is running (`python
        api.py`) and Neo4j is accessible/populated.
      </div>
    );
  }

  return (
    <div className="page-container">
      <h2>Shared Effects from Multiple Causes</h2>
      {sharedEffects.length > 0 ? (
        <div className="connection-grid">
          {sharedEffects.map((effect, index) => (
            <div key={index} className="connection-card">
              <h3>Effect: {effect.shared_effect}</h3>
              <p>
                <strong>Cause A:</strong> {effect.cause_a}
              </p>
              <p className="explanation">
                <em>Why A leads to Effect:</em> {effect.why_a_to_effect}
              </p>
              <p>
                <strong>Cause B:</strong> {effect.cause_b}
              </p>
              <p className="explanation">
                <em>Why B leads to Effect:</em> {effect.why_b_to_effect}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="page-message">
          No shared effects found. Check if Neo4j is populated with
          LLM-extracted data.
        </p>
      )}
    </div>
  );
};

export default SharedEffectsPage;
