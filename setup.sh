#!/bin/bash

# Define directories
NEO4J_HOME_DIR="./neo4j"
NEO4J_PLUGINS_DIR="${NEO4J_HOME_DIR}/plugins"
APOC_VERSION="4.4.0.12" # Match with Neo4j version in docker-compose.yml
APOC_DOWNLOAD_URL="https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/${APOC_VERSION}/apoc-${APOC_VERSION}-all.jar"
APOC_JAR_FILENAME="apoc-${APOC_VERSION}-all.jar"
APOC_FULL_PATH="${NEO4J_PLUGINS_DIR}/${APOC_JAR_FILENAME}"

echo "Setting up Neo4j environment..."

# Create necessary directories if they don't exist
mkdir -p ${NEO4J_HOME_DIR}/data
mkdir -p ${NEO4J_HOME_DIR}/logs
mkdir -p ${NEO4J_HOME_DIR}/import
mkdir -p ${NEO4J_PLUGINS_DIR}

echo "Checking for APOC plugin..."
# Always attempt to download to ensure a fresh, uncorrupted version
# Remove existing plugin first to force a fresh download
if [ -f "${APOC_FULL_PATH}" ]; then
    echo "Existing APOC plugin found. Removing to ensure fresh download."
    rm "${APOC_FULL_PATH}"
fi

echo "Downloading APOC plugin for Neo4j ${APOC_VERSION}..."
# Use curl for downloading
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed. Please install curl to download the APOC plugin."
    echo "  On Debian/Ubuntu: sudo apt-get install curl"
    echo "  On CentOS/RHEL: sudo yum install curl"
    echo "  On Windows (Git Bash/WSL): curl usually comes with Git Bash or can be installed via package manager."
    exit 1
fi
MAX_RETRIES=3
RETRY_COUNT=0
DOWNLOAD_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Attempting download (Attempt $((RETRY_COUNT+1)))..."
    curl -L --progress-bar -o "${APOC_FULL_PATH}" "${APOC_DOWNLOAD_URL}"
    if [ $? -eq 0 ]; then
        echo "APOC plugin downloaded successfully."
        DOWNLOAD_SUCCESS=true
        break
    else
        echo "Download failed. Retrying in 5 seconds..."
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 10
    fi
done

if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "Error: Failed to download APOC plugin after $MAX_RETRIES attempts. Please check the URL and your internet connection."
    exit 1
fi

echo "Starting Neo4j Docker container with Docker Compose..."
docker compose up -d

if [ $? -eq 0 ]; then
    echo "Neo4j container started successfully."
    echo "Waiting for Neo4j to be ready (this may take a moment)..."
    # Basic check to see if Neo4j is responsive, though healthcheck is defined in docker-compose
    # Loop until Neo4j is responsive on port 7474
    # Loop until Neo4j is responsive on the Bolt port (7687)
    # Increase the number of retries and sleep duration for more robustness
    for i in {1..15}; do # 15 iterations * 5 seconds = 75 seconds
        if nc -z localhost 7687 &> /dev/null; then # Check if Bolt port is open
            echo "Neo4j is ready! Access Neo4j Browser at http://localhost:7474"
            exit 0
        fi
        sleep 5
    done
    echo "Neo4j did not become ready in time."
    echo "Attempting to retrieve Docker logs for diagnosis:"
    docker compose logs neo4j
    exit 1
else
    echo "Error starting Neo4j container. Attempting to retrieve Docker logs:"
    docker compose logs neo4j
    exit 1
fi
