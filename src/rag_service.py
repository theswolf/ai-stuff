import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()
logger = logging.getLogger(__name__)


class RAGService:
    SYSTEM_PROMPT = """Sei un assistente preciso e utile. Rispondi alle domande
basandoti ESCLUSIVAMENTE sul contesto fornito. Se l'informazione non è presente
nel contesto, dì esplicitamente 'Non ho informazioni su questo argomento nei documenti forniti.'

Contesto:
{context}

Domanda: {question}

Risposta:"""

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""])
        self.vectorstore: Optional[Chroma] = None
        self._load_existing_vectorstore()

    def _load_existing_vectorstore(self) -> None:
        if Path(self.persist_directory).exists():
            try:
                self.vectorstore = Chroma(collection_name=self.collection_name, embedding_function=self.embeddings, persist_directory=self.persist_directory)
            except Exception as e:
                logger.warning(f"Impossibile caricare vectorstore: {e}")

    def ingest_documents(self, source: str) -> dict:
        source_path = Path(source)
        if source_path.is_dir():
            loader = DirectoryLoader(str(source_path), glob="**/*.{pdf,txt,md}", show_progress=True)
        elif source_path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(source_path))
        else:
            loader = TextLoader(str(source_path), encoding="utf-8")
        raw_documents = loader.load()
        chunks = self.text_splitter.split_documents(raw_documents)
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(documents=chunks, embedding=self.embeddings, collection_name=self.collection_name, persist_directory=self.persist_directory)
        else:
            self.vectorstore.add_documents(chunks)
        return {"source": str(source_path), "documents_loaded": len(raw_documents), "chunks_created": len(chunks), "total_in_store": self.vectorstore._collection.count()}

    def query(self, question: str, k: int = 4, return_sources: bool = True) -> dict:
        if self.vectorstore is None:
            raise ValueError("Nessun documento indicizzato. Chiamare ingest_documents() prima.")
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})
        prompt = PromptTemplate(template=self.SYSTEM_PROMPT, input_variables=["context", "question"])
        qa_chain = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=retriever, return_source_documents=return_sources, chain_type_kwargs={"prompt": prompt})
        result = qa_chain.invoke({"query": question})
        response = {"answer": result["result"]}
        if return_sources and "source_documents" in result:
            response["sources"] = [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata} for doc in result["source_documents"]]
        return response

    def get_stats(self) -> dict:
        if self.vectorstore is None:
            return {"status": "empty", "documents": 0}
        return {"status": "ready", "documents": self.vectorstore._collection.count(), "collection": self.collection_name, "persist_directory": self.persist_directory}
