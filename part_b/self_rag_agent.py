import os
from dotenv import load_dotenv
load_dotenv()
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.documents import Document
from graph import SelfRAGGraph

def setup_knowledge_base():
    """Ingest PDFs and create vector store."""
    data_dir = "Data_share"
    
    # Check if vector DB already exists locally (optional optimization)
    persist_directory = "./chroma_db"
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    if os.path.exists(persist_directory):
        print("Loading existing vector store...")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 3})

    print("Building knowledge base from PDFs...")
    documents = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(data_dir, filename)
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            
            # Add metadata based on filename
            doc_type = "course_catalog" if "Catalog" in filename else "faculty" if "Faculty" in filename else "policies"
            dept = "CS" if "CS_" in filename else "EE" if "EE_" in filename else "BBA" if "BBA_" in filename else "University"
            
            for d in docs:
                d.metadata["department"] = dept
                d.metadata["doc_type"] = doc_type
            
            documents.extend(docs)

    # Chunking strategy
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def main():
    print("Initializing Self-RAG Agent...")
    
    try:
        retriever = setup_knowledge_base()
        
        # Initialize LLM
        # Assumes GEMINI_API_KEY or GOOGLE_API_KEY is in environment
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        
        # Build Graph
        builder = SelfRAGGraph(llm, retriever)
        graph = builder.build()
        
        print("\nAgent ready! Type 'quit' or 'exit' to stop.")
        print("-" * 50)
        
        while True:
            query = input("\nUser Query: ")
            if query.lower() in ['quit', 'exit']:
                break
                
            inputs = {
                "question": query,
                "retries": 0,
                "web_fallback": False,
                "documents": []
            }
            
            print("\n--- EXECUTION TRACE ---")
            for output in graph.stream(inputs, stream_mode="updates"):
                for key, value in output.items():
                    print(f"Finished node: '{key}'")
            
            # Fetch final generation
            final_state = graph.get_state(graph.thread_id).values if hasattr(graph, 'thread_id') else inputs # this line might fail if memory isn't used
            
            # Actually, stream returns the latest updates. We can capture it
            # The final output is in the last node's updates.
            final_generation = value.get("generation", "No generation produced.")
            
            print("\n--- FINAL RESPONSE ---")
            print(final_generation)
            
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    main()
