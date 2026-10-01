# Building a localized, open-source RAG pipeline

This project is designed to map your existing Python and Docker skills onto AI infrastructure.

For this stack, we will use Qdrant as the vector database because of its lightweight nature and native filtering performance, alongside Ollama for running the model and embeddings locally.

We will use pure Python clients rather than high-level frameworks like LangChain to ensure you understand exactly how the components interface over HTTP APIs.

>This project has been designed for building on our CentOS VM, it requires minimal resources to operate, but will take advantage of any resources you can allocate. It is recommended that you provide 4x CPU cores, and 8GB RAM.

## Infrastructure Setup (docker-compose.yml)

We will spin up two services in a dedicated bridge network: Ollama and Qdrant.

Create a project directory and add the following docker-compose.yml file:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama_service
    ports:
      - "11434:11434"
    volumes:
      - ollama_storage:/root/.ollama
    # If using an NVIDIA GPU, uncomment this deployment block:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant_service
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  ollama_storage:
  qdrant_storage:
```

### Pull the Models

Launch your stack using `sudo docker compose up -d`, the Ollama container is ~3GB so may take a while.

Once healthy, execute the following commands to instruct the Ollama container to download your embedding model and your LLM:  

```bash
# Pull the text embedding model (produces a 768-dimension vector)
sudo docker exec -it ollama_service ollama pull nomic-embed-text

# Pull the lightweight language model for text generation
sudo docker exec -it ollama_service ollama pull llama3.2
```

>The embedding model is <300MB, but the language model is ~2GB, so may take a little while depending on your internet connection bandwidth.

## The Python Core Implementation

Set up a virtual environment and install the two official clients:

```bash
pip install qdrant-client ollama
```

Create a file named rag_pipeline.py and add the below code. The script breaks down the two essential architectural phases of RAG: Ingestion (Indexing) and Querying (Retrieval & Generation).

```py
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration constants
QDRANT_HOST = "http://localhost:6333"
OLLAMA_HOST = "http://localhost:11434"
COLLECTION_NAME = "enterprise_knowledge"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"

# Initialize clients (check_compatibility=False silences version mismatch warnings)
qdrant_client = QdrantClient(url=QDRANT_HOST, check_compatibility=False)
ollama_client = ollama.Client(host=OLLAMA_HOST)

def init_vector_db():
    """Creates the Qdrant collection if it does not exist."""
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        print(f"Creating collection: {COLLECTION_NAME}")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

def ingest_documents(docs: list[str]):
    """Embeds raw text documents and inserts them into Qdrant."""
    init_vector_db()
    
    for idx, doc_text in enumerate(docs):
        response = ollama_client.embed(model=EMBED_MODEL, input=doc_text)
        vector = response['embeddings'][0]
        
        point = PointStruct(
            id=idx,
            vector=vector,
            payload={"text": doc_text}
        )
        
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])
    print(f"Successfully ingested {len(docs)} document chunks.")

def query_rag(user_question: str) -> str:
    """Retrieves context from Qdrant and prompts the LLM for an answer."""
    # Step 1: Embed query
    query_vector = ollama_client.embed(model=EMBED_MODEL, input=user_question)['embeddings'][0]
    
    # Step 2: Query Qdrant using the updated query_points API
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=2
    )
    
    # Step 3: Extract payload from search_results.points
    retrieved_contexts = [point.payload["text"] for point in search_results.points]
    context_block = "\n---\n".join(retrieved_contexts)
    
    # Step 4: Construct system prompt
    system_prompt = (
        "You are a helpful assistant. Use ONLY the provided Context below to answer the Question.\n"
        "If the context does not contain the answer, say 'I cannot find that in the local database.'\n\n"
        f"Context:\n{context_block}"
    )
    
    # Step 5: Generate response
    output = ollama_client.generate(
        model=LLM_MODEL,
        system=system_prompt,
        prompt=user_question
    )
    return output['response']

if __name__ == "__main__":
    internal_docs = [
        "Server room 2B requires the blue keycard for entry. Contact Mark from IT for provisioning.",
        "The production database undergoes a structural backup nightly at 02:00 UTC. It is stored on NFS share /mnt/backups.",
        "Our current Kubernetes staging cluster uses the Calico CNI for container network policy routing."
    ]
    
    print("Starting Ingestion...")
    ingest_documents(internal_docs)
    
    print("\nExecuting RAG Query...")
    question = "When does the database backup run and where does it go?"
    answer = query_rag(question)
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {answer}\n")
    
    unrelated_question = "What is the capital of France?"
    print(f"Question: {unrelated_question}")
    print(f"Answer: {query_rag(unrelated_question)}")
```

Run your RAG pipeline with `python rag_pipeline.py`

It may take a couple of minutes depending on the resources allocated to your VM, but you should get a response answering the questions near the bottom of the python file. If so try adding additional `internal_docs` and questions against those docs.

### Key Points

- **Network Isolation**: Because Ollama handles both text embedding generation and text completion, your Python app only needs two API targets (:11434 and :6333). In production, these services would be locked down entirely behind a private backend network tier with zero external ingress allowed.  

- **State Management**: Qdrant stores the text chunks directly alongside the semantic vectors within the payload property. This eliminates the architectural overhead of maintaining a relational database mapped over a standalone vector indexing server.

- **Deterministic Controls**: By strict styling of the system_prompt ("Use ONLY the provided Context..."), you mitigate hallucinations, turning the LLM from a generic creative writer into a precise lookup engine for the text returned by the mathematical search.
