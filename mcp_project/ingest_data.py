import os
import glob
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATA_DIR = "Initial_Data"
DB_DIR = "chroma_db"
COLLECTION_NAME = "academic_knowledge"


def load_documents():
    docs = []

    # Load Text files
    text_files = glob.glob(os.path.join(DATA_DIR, "*.txt"))
    for file in text_files:
        loader = TextLoader(file)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata["doc_type"] = "handbook"
            doc.metadata["department"] = "university"
            doc.metadata["priority_level"] = "high"
        docs.extend(loaded_docs)

    # Load CSV files
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for file in csv_files:
        loader = CSVLoader(file)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata["doc_type"] = "course_catalog"
            doc.metadata["department"] = "various"
            doc.metadata["priority_level"] = "medium"
        docs.extend(loaded_docs)

    return docs


def main():
    print("Loading documents...")
    documents = load_documents()
    print(f"Loaded {len(documents)} document pieces.")

    print("Chunking documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", " ", ""])
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Initializing Vector Database and indexing...")

    # Use fully free local embeddings via HuggingFace
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_DIR, collection_name=COLLECTION_NAME
    )
    print(f"Successfully indexed into {DB_DIR}.")


if __name__ == "__main__":
    main()
