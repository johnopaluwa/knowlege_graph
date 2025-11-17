from flask import Flask, jsonify
from flask_cors import CORS

from neo4j_query_api import (find_causal_chains,
                             find_shared_effects_from_multiple_causes,
                             get_graph_connection)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Initialize Neo4j connection
get_graph_connection()

@app.route('/')
def hello_world():
    return 'Hello, Flask API for Knowledge Graph!'

@app.route('/causal_chains', methods=['GET'])
def get_causal_chains():
    chains = find_causal_chains()
    return jsonify(chains)

@app.route('/shared_effects', methods=['GET'])
def get_shared_effects():
    shared_effects = find_shared_effects_from_multiple_causes()
    return jsonify(shared_effects)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
