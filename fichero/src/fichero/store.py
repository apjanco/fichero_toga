import chromadb
import pandas as pd
from tqdm import tqdm
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from chromadb.utils import embedding_functions
import random 


def create_chroma_client():
    """
    Create a ChromaDB client with a persistent storage path.
    """
    return chromadb.PersistentClient(path="chroma_db")

def test_chroma_client(self):
    """
    Test the ChromaDB client by creating a collection and adding documents.
    """
    client = create_chroma_client()
    
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="LaBSE")
    collection = client.get_or_create_collection(name="testing",embedding_function=sentence_transformer_ef)

    splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=5,model_name="LaBSE")


    collection.add(
        documents=[
            "This is a document about pineapple",
            "This is a document about oranges"
        ],
        ids=["id1", "id2"],
        metadatas=[
            {"fruit": "pineapple"},
            {"fruit": "orange"}
        ],
    )

    results = collection.query(
    query_texts=["This is a query document about hawaii"], # Chroma will embed this for you
    n_results=2 # how many results to return
    )
    print(results)