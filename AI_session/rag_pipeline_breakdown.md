# RAG Pipeline Breakdown

## Prior to Running our Python App

We deployed both Ollama and Qdrant (pronounced quadrant) as Docker containers:

- **Ollama** is simply an open-source application which allows you to run a number of AI models locally, including embedding models and LLMs.

- **Qdrant** is a vector database designed for storing high dimensional numerical representations of data, i.e. vectors, or *embeddings*. Qdrant operates with *Points* which consist of vectors and payloads (*optional*).

At a high level, we are going to use Ollama first to generate embeddings from 'company' data, store those vectors in Qdrant, then Ollama runs the Llama3.2 LLM to generate output text based on those embeddings.

## Code Breakdown

Below is a modular, section-by-section walkthrough, mapping the Python code directly to the core engineering concepts.

*Print statements and comments omitted for brevity*

```py
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
```

- `import ollama`
- `from qdrant_client import QdrantClient`
- `from qdrant_client.models import Distance, VectorParams, PointStruct`

These commands, like any Python import statements, import the associated libraries in order for us to interact with, in this case, Ollama and Qdrant, which we deployed as Docker containers.

- **QdrantClient**: Handles communication between our code and the Qdrant server
- **Distance**: Defines how Qdrant should calculate similarity between vectors - for text we typically measure with COSINE
- **VectorParams**: Defines the rules for a collection before it is created, including the number of dimensions, and the distance metric
- **PointStruct**: The package of individual vectors to be inserted into Qdrant, it includes:
  - **ID**: A unique number for the point
  - **Vector**: The actual list of numbers (embedding)
  - **Payload**: Optional JSON metadata to store with each point

```py
QDRANT_HOST = "http://localhost:6333"
OLLAMA_HOST = "http://localhost:11434"
COLLECTION_NAME = "enterprise_knowledge"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"
```

This block simply defines the endpoints for our Qdrant and Ollama Docker containers, names our collection, and specifies our two required models.

The pipeline communicates over HTTP endpoints **:6333** and **:11434**. This mimics enterprise architecture where the database and LLM inference engine run on separate scalable instances or cloud services.

```py
qdrant_client = QdrantClient(url=QDRANT_HOST, check_compatibility=False)
ollama_client = ollama.Client(host=OLLAMA_HOST)
```

Here we are initialising our clients; `check_compatibility=False` silences version mismatch warnings.

```py
def init_vector_db():
    ...
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        ...
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
```

This function initialises the Qdrant database, and creates the **collection**. You may think of the collection like a SQL table, it's a named set stored Points.

>This function is called by the `ingest_documents()` function

Our `COLLECTION_NAME` is set above, the `if` statement calls our `qdrant_client` object, and creates the collection if it does not already exist.

The client object's `.create_collection()` method is called, as noted above, the VectorParams are the rules for the collection, and are created **before** the collection is created:

- The size `768` must exactly match the output size of the embedding model
- The method used to calculate similarity between vectors is `Distance.COSINE`.

```py
def ingest_documents(docs: list[str]):
    ...
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
    ...
```

- `ingest_documents(docs: list[str])`: This function takes our `internal_docs` as `docs`, which we want to feed into our embeddings model.

  We also provide a **type hint** `list[str]` describing the expected format.
- `init_vector_db()`: Calls the function we described above to initialise our Qdrant DB, it does not require any parameters.
- `for idx, doc_text in enumerate(docs):`: In this for loop each item in our `internal_docs` list is indexed by `enumerate`, the index is `idx` and `doc_text` is the text value of the item.
  - To illustrate, `["Apple", "Banana", "Cherry"]` would produce:
    - Loop 1: `idx` = 0, `doc_text` = "Apple"
    - Loop 2: `idx` = 1, `doc_text` = "Banana"
    - Loop 3: `idx` = 2, `doc_text` = "Cherry"
- `response = ollama_client.embed(model=EMBED_MODEL, input=doc_text)`: Calls the embedding function of our `ollama_client` object, providing the embedding model to use, and the input text to be embedded. The `.embed(...)` method returns a JSON object containing the 'embeddings', amongst other data.
- `vector = response['embeddings'][0]`: The response from `ollama_client.embed(...)` contains a list of embeddings, from which index 0 is assigned to the `vector` variable.
- `point = PointStruct(id=idx, vector=vector, payload={"text": doc_text})`: The PointStruct is now created from the values generated, it takes an ID, the vector, and the payload - which is the actual `doc_text` in this case.
- `qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])`: Finally, the `qdrant_client.upsert(...)` method will either update (if exists) or insert the collection into the Qdrant DB.

```py
def query_rag(user_question: str) -> str:
    ...
    query_vector = ollama_client.embed(model=EMBED_MODEL, input=user_question)['embeddings'][0]
    ...
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=2
    )
```

- `def query_rag(user_question: str) -> str:`: defines a `query_rag()` function, takes the `user_question` parameter and converts it to a vector using the same embedding model; We include a type hint for the parameter, and `-> str` defines the data type to be returned. The `user_question` is defined near the bottom of the script.
- `query_vector = ollama_client.embed(...)['embeddings'][0]`: Same as the `ingest_documents()` function, except only the `['embeddings'][0]` value is captured and assigned to `query_vector`, rather than returning the whole JSON object.
- `search_results = qdrant_client.query_points(...)`: This is one of the essential functions of Qdrant, where it returns the keys (*remember: like index cards*) that are most similar to the query, in this case the top 2 (`limit=2`) results.

```py
retrieved_contexts = [point.payload["text"] for point in search_results.points]
context_block = "\n---\n".join(retrieved_contexts)
```

- `retrieved_contexts...`: the points in the `search_results` object (from the `query_rag()` function) are iterated through by a for loop, with the payload of each point assigned to `retrieved_contents` - remember these are the embeddings of the user's question.
- `context_block...`: each point's payload is joined to populate the `context_block` object.

```py
    system_prompt = (
        "You are a helpful assistant. Use ONLY the provided Context below to answer the Question.\n"
        "If the context does not contain the answer, say 'I cannot find that in the local database.'\n\n"
        f"Context:\n{context_block}"
    )
```

The `system_prompt` is the guidance for the LLM, forcing it to act only on the `retrieved_contexts` rather than it's internal training data. The explicit instruction to return a "...cannot find..." message is a safeguard against hallucinations.

```py
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

This is where we activate our pipeline:

- The `ingest_documents()` function is called, passing our `internal_docs` for embedding
- The `query_rag()` function is called with our first question, which should be answerable from the training data - both the question and the answer are printed.
- The `query_rag()` function is called again with a question that cannot be answered by the `internal_docs`, to ensure the model doesn't hallucinate a response.

### The Full RAG Pipeline

```text
Query
  |
Embed
  |
Retrieve
  |
Augment Prompt
  |
Generate Response
```
