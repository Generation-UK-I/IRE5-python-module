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
        "Our current Kubernetes staging cluster uses the Calico CNI for container network policy routing.",
        "To use the nvidia block in the docker compose you may need the Nvidia toolkit"
    ]
    
    print("Starting Ingestion...")
    ingest_documents(internal_docs)
    
    print("\nExecuting RAG Query...")
    question = "When does the database backup run and where does it go?"
    answer = query_rag(question)
    question2 = "How do I get into server room 2B?"
    answer2 = query_rag(question2)
    question3 = "What do I need to use the nvidia block in docker compose?"
    answer3 = query_rag(question3)
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {answer}\n")
    print(f"\nQuestion: {question2}")
    print(f"Answer: {answer2}\n")
    print(f"\nQuestion: {question3}")
    print(f"Answer: {answer3}\n")
    
    unrelated_question = "What is the capital of France?"
    print(f"Question: {unrelated_question}")
    print(f"Answer: {query_rag(unrelated_question)}")