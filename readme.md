# Knowledge Graph of arXiv Papers

This project aims to construct a knowledge graph from arXiv research papers. It streamlines the process of downloading scientific paper data from Kaggle, extracting key information using Large Language Models (LLMs), and storing this structured knowledge in a Neo4j graph database.

## Features

- **Automated Data Download**: Fetches the arXiv dataset from Kaggle.
- **Neo4j Docker Setup**: Provides a Dockerized Neo4j environment with the APOC plugin pre-installed.
- **LLM-Powered Information Extraction**: Utilizes OpenRouter (compatible with OpenAI API) to identify equations, methodologies, technologies, and causal relationships from paper abstracts and full texts.
- **Knowledge Graph Construction**: Populates a Neo4j graph database with papers, authors, categories, and extracted scientific entities.
- **Configurable Processing**: Allows setting a limit on the number of papers processed for development and testing.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Docker & Docker Compose**: For running the Neo4j database.
    - [Install Docker Engine](https://docs.docker.com/engine/install/)
    - [Install Docker Compose](https://docs.docker.com/compose/install/)
2.  **`curl`**: Used by `setup.sh` to download the APOC plugin.
    - Most Linux systems have `curl` pre-installed. For Windows, `curl` is usually available in Git Bash or can be installed via package managers.
3.  **`netcat` (nc)**: Used by `setup.sh` for checking Neo4j readiness.
    - Most Linux systems have `netcat` pre-installed. For Windows, you may need to install a `netcat` equivalent (e.g., Ncat from Nmap suite or through WSL/Git Bash).
4.  **Python 3.8+**: For running the data processing scripts.
    - [Install Python](https://www.python.org/downloads/)
5.  **Kaggle API Token**: To download the arXiv dataset.
    - Go to your Kaggle account settings (`https://www.kaggle.com/<username>/account`).
    - Under the "API" section, click "Create New API Token" to download `kaggle.json`.
    - Place `kaggle.json` in `~/.kaggle/` (on Linux/macOS) or `C:\Users\<YourUsername>\.kaggle\` (on Windows).
6.  **OpenRouter API Key**: For LLM-powered information extraction.
    - [Get an OpenRouter API Key](https://openrouter.ai/docs#api-keys)
    - Create a `.env` file in the root directory of this project and add your key:
      ```
      OPENROUTER_API_KEY="your_openrouter_api_key_here"
      NEO4J_URI="bolt://localhost:7687"
      NEO4J_USERNAME="neo4j"
      NEO4J_PASSWORD="password"
      # Optional: Specify a different LLM model
      # OPENROUTER_MODEL="mistralai/mixtral-8x7b-instruct"
      ```

## Getting Started

Follow these steps to set up the project and build your knowledge graph:

### 1. Clone the Repository

```bash
git clone https://github.com/johnopaluwa/the_knowledge_graph.git
cd the_knowledge_graph
```

### 2. Set Up Neo4j with Docker

Use the provided `setup.sh` script to prepare the Neo4j environment and start the database. This will also download the necessary APOC plugin.

```bash
chmod +x setup.sh  # Make the script executable
./setup.sh
```

This command will:

- Create `neo4j/data`, `neo4j/logs`, `neo4j/import`, and `neo4j/plugins` directories.
- Download the APOC plugin JAR file into `neo4j/plugins` using `curl`.
- Start a Neo4j container in the background, accessible at `http://localhost:7474` (Neo4j Browser) and `bolt://localhost:7687` (Bolt port).
- It will wait for up to 75 seconds for the Neo4j database to become ready, by regularly checking the Bolt port (7687) using `netcat`. If Neo4j does not become ready in time, the script will attempt to retrieve and display the Docker logs for the Neo4j container to aid in debugging.
- The default credentials are `neo4j` for username and `password` for password (configured in `docker-compose.yml` and `.env`).

### 3. Download the arXiv Dataset

Use the Python script to download the arXiv dataset from Kaggle. This will create an `arxiv_dataset` folder (if it doesn't exist) and populate it with metadata and PDF files.

```bash
pip install -r requirements.txt # Make sure this file exists, assuming dependencies are listed here
python download_kaggle_data.py
```

_Note_: If `requirements.txt` does not exist, you will need to install the dependencies manually: `pandas`, `kaggle`, `python-dotenv`, `py2neo`, `openai`, `pymupdf`.

### 4. Build the Knowledge Graph

Once Neo4j is running and the dataset is downloaded, run the main script to process the data and populate the knowledge graph.

```bash
python script.py
```

This script will read the downloaded PDF files, extract information using the configured LLM, and store it in your Neo4j database. By default, it processes a limited number of papers (`PROCESSING_LIMIT` in `script.py`) for efficiency during development.

## Exploring the Knowledge Graph

After `script.py` completes, you can access the Neo4j Browser at `http://localhost:7474`. Log in with `neo4j`/`password` and explore your knowledge graph using Cypher queries.

Example Cypher queries:

- **List all papers:**
  ```cypher
  MATCH (p:Paper) RETURN p.title, p.arxiv_id LIMIT 10
  ```
- **Find papers authored by a specific person:**
  ```cypher
  MATCH (a:Author)-[:AUTHORED]->(p:Paper) WHERE a.name = "Isaac Newton" RETURN p.title
  ```
- **Show relationships of a paper:**
  ```cypher
  MATCH (p:Paper)-[r]->(n) WHERE p.title = "Example Title" RETURN p, r, n
  ```
- **List equations mentioned in papers:**
  ```cypher
  MATCH (e:Equation) RETURN e.name LIMIT 10
  ```

## Stopping Neo4j

To stop the Neo4j container, run:

```bash
docker compose down
```

This will stop and remove the container, but preserve the data in the `neo4j/data` volume.
