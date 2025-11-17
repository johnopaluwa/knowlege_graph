import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [sharedEffects, setSharedEffects] = useState([]);
  const [causalChains, setCausalChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch Shared Effects
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

        // Fetch Causal Chains
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
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="Loading-Screen">
        Loading knowledge graph connections...
      </div>
    );
  }

  if (error) {
    return (
      <div className="Error-Screen">
        Error: {error.message}. Make sure the Flask API is running (`python
        api.py`) and Neo4j is accessible/populated.
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>ArXiv Knowledge Graph Connections</h1>
      </header>
      <main>
        <section className="Connections-Section">
          <h2>Shared Effects from Multiple Causes:</h2>
          {sharedEffects.length > 0 ? (
            <div className="Connection-List">
              {sharedEffects.map((effect, index) => (
                <div key={index} className="Connection-Card">
                  <h3>Effect: {effect.shared_effect}</h3>
                  <p>
                    <strong>Cause A:</strong> {effect.cause_a}
                  </p>
                  <p className="Explanation">
                    <em>Why A leads to Effect:</em> {effect.why_a_to_effect}
                  </p>
                  <p>
                    <strong>Cause B:</strong> {effect.cause_b}
                  </p>
                  <p className="Explanation">
                    <em>Why B leads to Effect:</em> {effect.why_b_to_effect}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="No-Data">
              No shared effects found. Check if Neo4j is populated with
              LLM-extracted data.
            </p>
          )}
        </section>

        <section className="Connections-Section">
          <h2>
            Causal Chains (Cause &#8594; Intermediate Effect &#8594; Final
            Effect):
          </h2>
          {causalChains.length > 0 ? (
            <div className="Connection-List">
              {causalChains.map((chain, index) => (
                <div key={index} className="Connection-Card">
                  <p>
                    <strong>Initial Cause:</strong> {chain.initial_cause}
                  </p>
                  <p className="Explanation">
                    <em>Why it leads to Intermediate Effect:</em>{" "}
                    {chain.explanation_step1}
                  </p>
                  <p>
                    <strong>Intermediate Effect:</strong>{" "}
                    {chain.intermediate_effect}
                  </p>
                  <p className="Explanation">
                    <em>Why it leads to Final Effect:</em>{" "}
                    {chain.explanation_step2}
                  </p>
                  <p>
                    <strong>Final Effect:</strong> {chain.final_effect}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="No-Data">
              No causal chains found. Check if Neo4j is populated with
              LLM-extracted data.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
