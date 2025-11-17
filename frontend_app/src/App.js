import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import "./App.css"; // Overall application styling
import Navbar from "./components/Navbar";
import CausalChainsPage from "./pages/CausalChainsPage";
import SharedEffectsPage from "./pages/SharedEffectsPage";

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <Routes>
          <Route path="/shared-effects" element={<SharedEffectsPage />} />
          <Route path="/causal-chains" element={<CausalChainsPage />} />
          {/* Default route for the homepage, can be a dashboard or redirect */}
          <Route path="/" element={<HomeContent />} />
        </Routes>
      </div>
    </Router>
  );
}

// Simple HomeContent component for the root path
const HomeContent = () => (
  <div className="home-container">
    <h2>Welcome to the ArXiv Knowledge Graph Explorer!</h2>
    <p>
      Explore shared effects and causal chains extracted from scientific papers.
      Use the navigation above to get started.
    </p>
    <p className="hint">
      Make sure your Flask API is running (`python api.py`) and Neo4j is
      accessible/populated for data to display correctly.
    </p>
  </div>
);

export default App;
