import { useCallback, useEffect, useRef, useState } from "react";
import { ForceGraph2D } from "react-force-graph"; // Corrected import
import "./Pages.css"; // Shared CSS for pages

const GraphVisualizationPage = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fgRef = useRef();

  // Helper function to process raw data into graph format
  const processDataToGraph = (causalChains, sharedEffects) => {
    const nodes = {};
    const links = [];

    const addNode = (id, label, type) => {
      if (!nodes[id]) {
        nodes[id] = { id: id, label: label, type: type, val: 1 };
      }
    };

    causalChains.forEach((chain) => {
      const causeId = `cause-${chain.initial_cause}`;
      const intermediateId = `effect-${chain.intermediate_effect}`;
      const finalId = `effect-${chain.final_effect}`;

      addNode(causeId, chain.initial_cause, "Cause");
      addNode(intermediateId, chain.intermediate_effect, "Effect");
      addNode(finalId, chain.final_effect, "Effect");

      links.push({
        source: causeId,
        target: intermediateId,
        relation: "CAUSES",
        why: chain.explanation_step1,
      });
      links.push({
        source: intermediateId,
        target: finalId,
        relation: "CAUSES",
        why: chain.explanation_step2,
      });
    });

    sharedEffects.forEach((effect) => {
      const effectId = `effect-${effect.shared_effect}`;
      const causeAId = `cause-${effect.cause_a}`;
      const causeBId = `cause-${effect.cause_b}`;

      addNode(effectId, effect.shared_effect, "Effect");
      addNode(causeAId, effect.cause_a, "Cause");
      addNode(causeBId, effect.cause_b, "Cause");

      links.push({
        source: causeAId,
        target: effectId,
        relation: "CAUSES",
        why: effect.why_a_to_effect,
      });
      links.push({
        source: causeBId,
        target: effectId,
        relation: "CAUSES",
        why: effect.why_b_to_effect,
      });
    });

    return {
      nodes: Object.values(nodes).map((node) => ({
        ...node,
        id: node.id,
        name: node.label, // react-force-graph uses 'name' for default label
      })),
      links: links,
    };
  };

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [causalChainsResponse, sharedEffectsResponse] = await Promise.all(
          [
            fetch("http://localhost:5000/causal_chains"),
            fetch("http://localhost:5000/shared_effects"),
          ]
        );

        if (!causalChainsResponse.ok)
          throw new Error(
            `HTTP error! status: ${causalChainsResponse.status} for causal chains`
          );
        if (!sharedEffectsResponse.ok)
          throw new Error(
            `HTTP error! status: ${sharedEffectsResponse.status} for shared effects`
          );

        const causalChainsData = await causalChainsResponse.json();
        const sharedEffectsData = await sharedEffectsResponse.json();

        setGraphData(processDataToGraph(causalChainsData, sharedEffectsData));
      } catch (error) {
        setError(error);
        console.error("Error fetching or processing graph data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const getNodeColor = useCallback((node) => {
    return node.type === "Cause" ? "#FF6347" : "#00CED1"; // Tomato for Causes, DarkTurquoise for Effects
  }, []);

  const getLinkColor = useCallback((link) => {
    return "#888"; // Gray for links
  }, []);

  const onNodeClick = useCallback((node) => {
    // Center on node and zoom in
    fgRef.current.centerAndZoom(node.x, node.y, 4);
    // You could also display node details here in a sidebar
    console.log("Clicked node:", node);
  }, []);

  if (loading) {
    return <div className="page-message">Loading graph data...</div>;
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
    <div className="page-container graph-page">
      <h2>Knowledge Graph Visualization</h2>
      {graphData.nodes.length > 0 ? (
        <div style={{ height: "700px", width: "100%" }}>
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            nodeLabel="name"
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            onNodeClick={onNodeClick}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(
                (n) => n + fontSize * 0.2
              ); // some padding

              ctx.fillStyle = "rgba(255, 255, 255, 0.9)"; // Slightly more opaque background
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y - bckgDimensions[1] / 2,
                bckgDimensions[0],
                bckgDimensions[1]
              );

              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = getNodeColor(node); // Use the custom node color function
              ctx.fillText(label, node.x, node.y);

              node.__bckgDimensions = bckgDimensions; // for hit testing
            }}
            nodeCanvasObjectMode={() => "after"} // Render labels after nodes
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.fillStyle = color;
              const bckgDimensions = node.__bckgDimensions;
              bckgDimensions &&
                ctx.fillRect(
                  node.x - bckgDimensions[0] / 2,
                  node.y - bckgDimensions[1] / 2,
                  bckgDimensions[0],
                  bckgDimensions[1]
                );
            }}
            linkColor={getLinkColor} // Use the custom link color function
            backgroundColor="#F0F2F5"
            enableNodeDrag={true}
            d3AlphaDecay={0.04} // Reduce alpha decay to make forces settle slower
            d3VelocityDecay={0.3} // Reduce velocity decay to maintain momentum
            // Adjust forces for better spread
            d3Force="charge"
            d3ForceOptions={{
              charge: { strength: -800 }, // Even stronger repulsion
              link: { distance: 100 }, // Even larger link distance
            }}
          />
        </div>
      ) : (
        <p className="page-message">
          No graph data found. Ensure Neo4j is populated with LLM-extracted data
          and Flask API is running.
        </p>
      )}
    </div>
  );
};

export default GraphVisualizationPage;
