import os
import sys

import kaggle

# Define the dataset to download
DATASET_NAME = "Cornell-University/arxiv"
DOWNLOAD_PATH = "arxiv_dataset" # This will create a folder named 'arxiv_dataset'

def download_arxiv_dataset():
    print(f"Attempting to download dataset: {DATASET_NAME} to {os.path.abspath(DOWNLOAD_PATH)}")
    
    # Ensure the download directory exists
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    # Check if the metadata file already exists
    metadata_filepath = os.path.join(DOWNLOAD_PATH, "arxiv-metadata-oai-snapshot.json")
    if os.path.exists(metadata_filepath):
        print(f"Metadata file '{metadata_filepath}' already exists. Skipping download.")
        return

    try:
        # Initialize Kaggle API client
        kaggle.api.authenticate()
        
        # Download all files from the dataset
        # The 'path' argument specifies the directory where files will be extracted
        kaggle.api.dataset_download_files(DATASET_NAME, path=DOWNLOAD_PATH, unzip=True)
        print(f"Dataset '{DATASET_NAME}' downloaded and unzipped successfully to '{DOWNLOAD_PATH}'.")
    except Exception as e:
        print(f"An error occurred during download: {e}", file=sys.stderr)
        print("Please ensure your kaggle.json is correctly placed in ~/.kaggle/ (or C:\\Users\\<YourUsername>\\.kaggle\\ on Windows)", file=sys.stderr)
        print("and contains valid credentials.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    download_arxiv_dataset()
