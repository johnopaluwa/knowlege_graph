import json
import os
import sys
import time

import fitz  # PyMuPDF
import openai  # OpenRouter is OpenAI API compatible
import pandas as pd  # Import pandas for data handling
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship

# Load environment variables from .env file
load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please add it to your .env file.")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mixtral-8x7b-instruct") # Default to Mixtral if not set

# Global processing limit for testing
PROCESSING_LIMIT = 100 

llm_client = openai.OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Connect to Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Clear existing data and relationships (optional, for development purposes)
graph.run("MATCH (n) DETACH DELETE n;")

# Create constraints for uniqueness and faster lookups
# These will only be created if they don't already exist
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.arxiv_id IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.term IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equation) REQUIRE e.name IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Methodology) REQUIRE m.name IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cause) REQUIRE c.description IS UNIQUE")
graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Effect) REQUIRE f.description IS UNIQUE")


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    Returns the extracted text as a string.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}", file=sys.stderr)
        return None
    
    text_content = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_content += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}", file=sys.stderr)
        # For problematic PDFs, return an empty string to avoid LLM errors with malformed text
        return "" 
    return text_content


def sanitize_text_for_llm(text):
    """
    Removes or replaces problematic characters for LLM APIs,
    especially control characters or unescaped newlines that might break JSON.
    """
    if not text:
        return ""
    # Remove non-ASCII characters
    cleaned_text = text.encode('ascii', 'ignore').decode('ascii')
    # Replace common control characters (like form feed) and normalize whitespace
    cleaned_text = ' '.join(cleaned_text.split())
    # Optionally, escape JSON-breaking characters if the API expects strict JSON strings in content.
    # For now, relying on 'ignore' and whitespace normalization might be enough.
    # If errors persist, more aggressive escaping might be needed (e.g., json.dumps)
    return cleaned_text


def load_arxiv_metadata_from_json(filepath):
    """Loads arXiv metadata from the Kaggle JSON file."""
    # The Kaggle JSON is a single large file with one JSON object per line, not a single JSON array.
    # We'll read it line by line.
    
    # For full dataset, consider using Dask or Spark, or process in chunks.
    metadata_records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            # Process all records for scalability
            try:
                metadata_records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line {i}: {e}")
    return pd.DataFrame(metadata_records)


def get_arxiv_id_from_pdf_filename(pdf_filename):
    """
    Extracts the arXiv ID from a PDF filename.
    Assumes filename format like '1701.00001.pdf' or '1701.00001v1.pdf'.
    """
    if pdf_filename.endswith('.pdf'):
        base_name = pdf_filename[:-4] # Remove '.pdf'

    # Remove version suffix if present (e.g., '1701.00001v1' -> '1701.00001')
    if 'v' in base_name and base_name.count('v') == 1 and base_name.split('v')[1].isdigit():
        return base_name.split('v')[0]
    return base_name


def analyze_text_with_llm(text):
    """Uses LLM (via OpenRouter) to extract equations, methodologies, and technologies from text."""
    # Truncate text to fit within typical LLM context windows (e.g., 8192 for Mixtral)
    # This is a simplification; for production, more intelligent chunking/summarization is needed.
    max_llm_tokens = 6000 # Roughly 6000 tokens for text, leaving room for prompt and response
    if len(text.split()) > max_llm_tokens:
        text = " ".join(text.split()[:max_llm_tokens])
        print(f"Warning: Text truncated to {max_llm_tokens} tokens for LLM processing.")

    prompt_messages = [
        {"role": "system", "content": """You are an expert at extracting key scientific information from research papers. 
From the following research paper text, identify and list any explicitly mentioned equations (names or descriptive phrases), specific methodologies, novel technologies, and cause-and-effect relationships. For cause-and-effect relationships, include an explanation of *why* the cause leads to the effect.
If an item is not found, return an empty list for that category.

Return your answer as a JSON object with the following keys:
"equations": ["equation_name_or_description", ...],
"methodologies": ["methodology_name_or_description", ...],
"technologies": ["technology_name_or_description", ...],
"causal_relationships": [
    {
        "cause": "description of cause",
        "effect": "description of effect",
        "why": "explanation of why the cause leads to the effect, incorporating underlying mechanisms or concepts"
    }
]"""},
        {"role": "user", "content": f"Paper Text:\n{json.dumps(text)}"} # Use json.dumps to properly escape text
    ]

    try:
        # Use OpenRouter for the chat completion
        chat_completion = llm_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=prompt_messages,
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        llm_output = chat_completion.choices[0].message.content
        return json.loads(llm_output)
    except json.JSONDecodeError as e:
        print(f"Error decoding LLM response for text analysis: {e}. Raw LLM output: {llm_output[:500]}...", file=sys.stderr)
        return {"equations": [], "methodologies": [], "technologies": []}
    except Exception as e:
        print(f"General error calling LLM for text analysis: {e}", file=sys.stderr)
        return {"equations": [], "methodologies": [], "technologies": []}


def create_knowledge_graph_from_local_data(metadata_df, arxiv_dataset_base_path="arxiv_dataset"):
    """
    Populates the Neo4j knowledge graph from local Kaggle PDFs and corresponding metadata.
    This version iterates through PDF files first.
    """
    pdf_dir = os.path.join(arxiv_dataset_base_path, "pdf")
    if not os.path.exists(pdf_dir):
        print(f"Error: PDF directory not found at {pdf_dir}. Please ensure the Kaggle dataset is fully downloaded.", file=sys.stderr)
        return

    # Create a mapping from arxiv_id to metadata for quick lookups
    metadata_map = metadata_df.set_index('id')

    processed_count = 0
    for root, _, files in os.walk(pdf_dir):
        for filename in files:
            if processed_count >= PROCESSING_LIMIT: # Apply global limit
                print(f"Reached processing limit of {PROCESSING_LIMIT} files.")
                break
            
            if filename.endswith(".pdf"):
                pdf_filepath = os.path.join(root, filename)
                arxiv_id = get_arxiv_id_from_pdf_filename(filename)

                if arxiv_id and arxiv_id in metadata_map.index:
                    paper_meta = metadata_map.loc[arxiv_id]
                    # Ensure paper_meta is a Series rather than a DataFrame if multiple exist or if it's a scalar value.
                    # When metadata_map.loc[arxiv_id] is called, if arxiv_id is unique, it returns a Series.
                    # If there are duplicate indices, it returns a DataFrame.
                    # If the metadata_df had only one column BEFORE set_index, it might return a scalar.
                    
                    # Let's ensure paper_meta is always a Series for consistent access.
                    if isinstance(paper_meta, pd.DataFrame):
                        if not paper_meta.empty:
                            paper_meta = paper_meta.iloc[0]
                        else:
                            print(f"Warning: No metadata found for arxiv_id {arxiv_id} despite being in index. Skipping.", file=sys.stderr)
                            continue
                    elif not isinstance(paper_meta, pd.Series):
                        # This handles cases where .loc might sometimes return a raw value if the original DataFrame was single-column
                        # However, with multiple columns typically in arxiv-metadata, this is less likely.
                        # Still, it's safer to ensure it's a Series or DataFrame which can be converted.
                        print(f"Error: unexpected type for paper_meta after lookup. Type: {type(paper_meta)}, Value: {paper_meta}", file=sys.stderr)
                        continue

                    print(f"DEBUG: Type of paper_meta: {type(paper_meta)}")
                    if isinstance(paper_meta, pd.Series):
                        print(f"DEBUG: Keys in paper_meta: {list(paper_meta.index)}")
                    
                    print(f"Processing PDF: {filename} (arXiv ID: {arxiv_id})")
                    
                    paper = {}
                    # Safely access 'id' and other fields
                    paper['arxiv_id'] = paper_meta.get('id', arxiv_id) # Fallback to arxiv_id from filename if 'id' not in meta
                    paper['title'] = paper_meta.get('title', 'No Title Found')
                    paper['summary'] = paper_meta.get('abstract', 'No Abstract Found') # Safely access abstract
                    
                    # Safely extract version information including URL, published, updated dates
                    if 'versions' in paper_meta and isinstance(paper_meta['versions'], list) and len(paper_meta['versions']) > 0:
                        paper['published'] = paper_meta['versions'][0].get('created')
                        paper['updated'] = paper_meta['versions'][-1].get('created')
                        paper['url'] = paper_meta['versions'][-1].get('url')
                    else:
                        paper['published'] = None
                        paper['updated'] = None
                        paper['url'] = None

                    parsed_authors = []
                    author_string = paper_meta.get('authors', '')
                    author_names = [a.strip() for a in author_string.split(',') if a.strip()]
                    for name in author_names:
                        parsed_authors.append({"name": name, "affiliation": None})
                    paper['authors'] = parsed_authors

                    paper['categories'] = [cat.strip() for cat in paper_meta.get('categories', '').split() if cat.strip()]
                    paper['primary_category'] = paper['categories'][0] if paper['categories'] else None
                    
                    paper['journal_ref'] = paper_meta.get('journal_ref')
                    paper['doi'] = paper_meta.get('doi')

                    paper_node = Node(
                        "Paper",
                        arxiv_id=paper['arxiv_id'],
                        title=paper['title'],
                        summary=paper['summary'],
                        published=paper['published'],
                        updated=paper['updated'],
                        url=paper['url'],
                        doi=paper.get('doi'),
                        journal_ref=paper.get('journal_ref')
                    )
                    graph.merge(paper_node, "Paper", "arxiv_id")

                    for author_data in paper['authors']:
                        author_node = Node("Author", name=author_data['name'])
                        graph.merge(author_node, "Author", "name")
                        graph.create(Relationship(author_node, "AUTHORED", paper_node))

                    for category_term in paper['categories']:
                        category_node = Node("Category", term=category_term)
                        graph.merge(category_node, "Category", "term")
                        graph.create(Relationship(paper_node, "HAS_CATEGORY", category_node))

                    if 'primary_category' in paper and paper['primary_category']:
                        primary_category_node = Node("Category", term=paper['primary_category'])
                        graph.merge(primary_category_node, "Category", "term")
                        graph.create(Relationship(paper_node, "HAS_PRIMARY_CATEGORY", primary_category_node))
                    
                    full_text = extract_text_from_pdf(pdf_filepath)
                    text_for_llm_analysis = full_text if full_text and len(full_text.split()) > 100 else paper['summary'] 

                    if text_for_llm_analysis:
                        print(f"Analyzing text for {paper['title']} with LLM...")
                        extracted_data = analyze_text_with_llm(text_for_llm_analysis)
                        
                        for eq_name in extracted_data.get('equations', []):
                            equation_node = Node("Equation", name=eq_name)
                            graph.merge(equation_node, "Equation", "name")
                            graph.create(Relationship(paper_node, "MENTIONS_EQUATION", equation_node))
                        
                        for meth_name in extracted_data.get('methodologies', []):
                            methodology_node = Node("Methodology", name=meth_name)
                            graph.merge(methodology_node, "Methodology", "name")
                            graph.create(Relationship(paper_node, "MENTIONS_METHODOLOGY", methodology_node))
                            
                        for tech_name in extracted_data.get('technologies', []):
                            technology_node = Node("Technology", name=tech_name)
                            graph.merge(technology_node, "Technology", "name")
                            graph.create(Relationship(paper_node, "MENTIONS_TECHNOLOGY", technology_node))
        
                        for causal_rel in extracted_data.get('causal_relationships', []):
                            cause_desc = causal_rel.get('cause')
                            effect_desc = causal_rel.get('effect')
                            why_expl = causal_rel.get('why')

                            if cause_desc and effect_desc:
                                # Create Source (Cause) node and Target (Effect) node
                                cause_node = Node("Cause", description=cause_desc)
                                effect_node = Node("Effect", description=effect_desc)
                                
                                graph.merge(cause_node, "Cause", "description")
                                graph.merge(effect_node, "Effect", "description")
                                
                                # Link the paper to the identified cause and effect
                                graph.create(Relationship(paper_node, "IDENTIFIES_CAUSE", cause_node))
                                graph.create(Relationship(paper_node, "IDENTIFIES_EFFECT", effect_node))
                                
                                # Create the causal relationship itself with the "why" as a property
                                causal_relationship = Relationship(cause_node, "CAUSES", effect_node, why=why_expl)
                                graph.create(causal_relationship)
                            else:
                                print(f"Warning: Incomplete causal relationship found for paper {paper['arxiv_id']}: {causal_rel}", file=sys.stderr)
                    else:
                        print(f"No sufficient text available for LLM analysis for paper {paper['arxiv_id']}")
                    
                    time.sleep(0.1)
                    processed_count += 1
                else:
                    print(f"Skipping PDF {filename}: No metadata found for arXiv ID: {arxiv_id} or ID could not be extracted.")
    print(f"Finished processing {processed_count} PDFs for knowledge graph creation.")


if __name__ == "__main__":
    print("Starting knowledge graph creation from local Kaggle dataset with PDF-first and LLM analysis...")
    try:
        kaggle_dataset_path = "arxiv_dataset"
        metadata_filepath = os.path.join(kaggle_dataset_path, "arxiv-metadata-oai-snapshot.json")
        
        # Check if the PDF directory exists and is not empty
        pdf_directory = os.path.join(kaggle_dataset_path, "pdf")
        if not os.path.exists(pdf_directory) or not os.listdir(pdf_directory):
            print(f"Error: PDF directory '{pdf_directory}' is missing or empty. Please ensure 'download_kaggle_data.py' has been run successfully and PDFs are present.", file=sys.stderr)
            sys.exit(1)
            
        
        if not os.path.exists(metadata_filepath):
            print(f"Error: Metadata file not found at {metadata_filepath}. Please ensure the Kaggle dataset is fully downloaded.", file=sys.stderr)
            print("You need to run 'python download_kaggle_data.py' first.", file=sys.stderr)
            exit(1)

        print(f"Loading metadata from {metadata_filepath}...")
        arxiv_metadata_df = load_arxiv_metadata_from_json(metadata_filepath)
        print(f"Loaded {len(arxiv_metadata_df)} metadata records.")

        create_knowledge_graph_from_local_data(arxiv_metadata_df, kaggle_dataset_path)
        
        print("Knowledge graph created successfully with local full-text LLM analysis! You can now access Neo4j Browser at http://localhost:7474 and explore the data.")
    except Exception as e:
        print(f"An unexpected error occurred while processing knowledge graph: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr) # Print detailed traceback
        sys.exit(1)
