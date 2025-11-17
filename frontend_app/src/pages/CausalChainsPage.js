import { useEffect, useState } from "react";
import "./Pages.css"; // Shared CSS for pages

const CausalChainsPage = () => {
  const [causalChains, setCausalChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const causalChainsResponse = await fetch(
          "http://localhost:5000/causal_chains"
        );
        if (!causalChainsResponse.ok) {
          throw new Error(`HTTP error! status: ${causalChainsResponse.status}`);
        }
        const causalChainsData = await causalChainsResponse.json();
        setCausalChains(causalChainsData);
      } catch (error) {
        setError(error);
        console.error("Error fetching causal chains data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return <div className="page-message">Loading causal chains...</div>;
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
      <h2>
        Causal Chains (Cause &#8594; Intermediate Effect &#8594; Final Effect)
      </h2>
      {causalChains.length > 0 ? (
        <div className="connection-grid">
          {causalChains.map((chain, index) => (
            <div key={index} className="connection-card">
              <p>
                <strong>Initial Cause:</strong> {chain.initial_cause}
              </p>
              <p className="explanation">
                <em>Why it leads to Intermediate Effect:</em>{" "}
                {chain.explanation_step1}
              </p>
              <p>
                <strong>Intermediate Effect:</strong>{" "}
                {chain.intermediate_effect}
              </p>
              <p className="explanation">
                <em>Why it leads to Final Effect:</em> {chain.explanation_step2}
              </p>
              <p>
                <strong>Final Effect:</strong> {chain.final_effect}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="page-message">
          No causal chains found. Check if Neo4j is populated with LLM-extracted
          data.
        </p>
      )}
    </div>
  );
};

export default CausalChainsPage;
