import json
import os

from dotenv import load_dotenv
from py2neo import Graph, Relationship

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

graph = None

def get_graph_connection():
    global graph
    if graph is None:
        try:
            graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            # Test connection
            graph.run("RETURN 1").data()
            print("Successfully connected to Neo4j.")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            graph = None
    return graph

def find_causal_chains(limit=20):
    """
    Finds causal chains in the graph: Cause -> Effect1 -> Effect2.
    """
    query = f"""
    MATCH (c1:Cause)-[r1:CAUSES]->(e1:Effect)
    MATCH (e1)-[r2:CAUSES]->(e2:Effect)
    RETURN
        c1.description AS initial_cause,
        e1.description AS intermediate_effect,
        e2.description AS final_effect,
        r1.why AS why1,
        r2.why AS why2
    LIMIT {limit}
    """
    
    results = []
    db_graph = get_graph_connection()
    if db_graph:
        for record in db_graph.run(query):
            results.append({
                "initial_cause": record["initial_cause"],
                "intermediate_effect": record["intermediate_effect"],
                "final_effect": record["final_effect"],
                "explanation_step1": record["why1"],
                "explanation_step2": record["why2"]
            })
    return results

def find_shared_effects_from_multiple_causes(limit=20):
    """
    Identifies effects that stem from multiple distinct causes.
    """
    query = f"""
    MATCH (c1:Cause)-[r1:CAUSES]->(e:Effect)<-[r2:CAUSES]-(c2:Cause)
    WHERE c1 <> c2
    RETURN
        e.description AS shared_effect,
        COLLECT(DISTINCT c1.description) AS cause1_list,
        COLLECT(DISTINCT c2.description) AS cause2_list // This won't work as expected if c1 and c2 are just names, needs to collect both sides and then merge
    LIMIT {limit}
    """
    # Revised query for shared effects
    query_revised = f"""
    MATCH (c1:Cause)-[r1:CAUSES]->(e:Effect)
    MATCH (c2:Cause)-[r2:CAUSES]->(e)
    WHERE id(c1) < id(c2) // Ensures we don't get duplicate pairs (c1,c2) and (c2,c1)
    RETURN
        e.description AS shared_effect,
        c1.description AS cause_A,
        c2.description AS cause_B,
        r1.why AS why_A_to_E,
        r2.why AS why_B_to_E
    LIMIT {limit}
    """
    
    results = []
    db_graph = get_graph_connection()
    if db_graph:
        for record in db_graph.run(query_revised):
            results.append({
                "shared_effect": record["shared_effect"],
                "cause_a": record["cause_A"],
                "cause_b": record["cause_B"],
                "why_a_to_effect": record["why_A_to_E"],
                "why_b_to_effect": record["why_B_to_E"]
            })
    return results


if __name__ == "__main__":
    print("Running example queries directly...")
    
    print("\n--- Causal Chains ---")
    chains = find_causal_chains(limit=5)
    if chains:
        for i, chain in enumerate(chains):
            print(f"Chain {i+1}:")
            print(f"  Initial Cause: {chain['initial_cause']}")
            print(f"  -> Intermediate Effect: {chain['intermediate_effect']} (Why: {chain['explanation_step1']})")
            print(f"  -> Final Effect: {chain['final_effect']} (Why: {chain['explanation_step2']})")
    else:
        print("No causal chains found (or Neo4j not connected/populated).")

    print("\n--- Shared Effects from Multiple Causes ---")
    shared_effects = find_shared_effects_from_multiple_causes(limit=5)
    if shared_effects:
        for i, effect_data in enumerate(shared_effects):
            print(f"Shared Effect {i+1}: {effect_data['shared_effect']}")
            print(f"  Cause A: {effect_data['cause_a']} (Why: {effect_data['why_a_to_effect']})")
            print(f"  Cause B: {effect_data['cause_b']} (Why: {effect_data['why_b_to_effect']})")
    else:
        print("No shared effects from multiple causes found (or Neo4j not connected/populated).")
